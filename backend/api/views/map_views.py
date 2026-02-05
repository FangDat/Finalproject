import requests
import datetime
import logging
from urllib.parse import urlencode
from django.http import HttpResponse
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import math
from django.conf import settings


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
         
# CONFIG
OPENWEATHER_API_KEY = settings.OPENWEATHER_API_KEY  
METADATA_CACHE_TIMEOUT = 300  # 5 phút
TILE_CACHE_TIMEOUT = 600      # 10 phút cache tile bytes
MAX_TIMESTAMP_RANGE_HOURS = 48

   
@api_view(["GET"])
@permission_classes([AllowAny])
def get_weather_map(request):
    """
    Trả metadata cho frontend — xác định endpoint tile proxy và timestamps cho timelapse.
    """
    # ❗ mặc định layer là precipitation thay vì clouds
    layer = (request.GET.get("layer") or "precipitation").lower()
    hours = int(request.GET.get("hours") or 24)
    interval_h = int(request.GET.get("interval_h") or 3)

    if hours < 1:
        hours = 24
    if hours > MAX_TIMESTAMP_RANGE_HOURS:
        hours = MAX_TIMESTAMP_RANGE_HOURS
    if interval_h < 1:
        interval_h = 1

    layer_map = {
        "clouds": "CL",
        "temp": "TA2",
        "wind": "WND",
        "precipitation": "PA0",  # Accumulated precipitation
    }

    if layer not in layer_map:
        logger.debug("get_weather_map: invalid layer requested: %s", layer)
        return Response({"error": "Invalid layer name"}, status=400)

    now = int(datetime.datetime.utcnow().timestamp())
    timestamps = []
    steps = max(1, int(hours / interval_h))
    for i in range(0, steps + 1):
        ts = now + i * interval_h * 3600
        timestamps.append(ts)

    cache_key = f"map:meta:{layer}:{hours}:{interval_h}"
    cached = cache.get(cache_key)
    if cached:
        cached["timestamps"] = timestamps
        return Response(cached)

    proxy_tile_endpoint = "/api/map/tile/?{qs}"

    # ✅ custom legend tĩnh (tự host)
    legend_map = {
        "temp": "/static/legend/temp_custom.png",
        "wind": "https://openweathermap.org/themes/openweathermap/assets/vendor/owm/img/widgets/wind_speed_scale.png",
        "clouds": "https://openweathermap.org/themes/openweathermap/assets/vendor/owm/img/widgets/clouds_scale.png",
        "precipitation": "https://openweathermap.org/themes/openweathermap/assets/vendor/owm/img/widgets/precipitation_scale.png",
    }

    metadata = {
        "layer": layer,
        "proxy_tile_endpoint_template": proxy_tile_endpoint,
        "timestamps": timestamps,
        "legend_url": legend_map.get(layer),
        "note": "Now using OpenWeatherMap API v2.0 (maps.openweathermap.org)."
    }

    cache.set(cache_key, metadata, timeout=METADATA_CACHE_TIMEOUT)
    return Response(metadata)


@api_view(["GET"])
@permission_classes([AllowAny])
def proxy_tile(request):
    """
    Proxy tile endpoint:
      /api/map/tile/?layer=temp&z=...&x=...&y=...&timestamp=...
    Backend sẽ gọi OpenWeatherMap 2.0 và trả ảnh tile PNG.
    """
    layer = (request.GET.get("layer") or "precipitation").lower()
    z = request.GET.get("z")
    x = request.GET.get("x")
    y = request.GET.get("y")
    timestamp = request.GET.get("timestamp")

    if not all([z, x, y]):
        return Response({"error": "Missing tile coordinates (z,x,y)."}, status=400)

    layer_map = {
        "temp": "TA2",
        "wind": "WND",
        "precipitation": "PA0"
    }

    if layer not in layer_map:
        return Response({"error": "Invalid layer name"}, status=400)

    if not timestamp:
        timestamp = str(int(datetime.datetime.utcnow().timestamp()))

    # ✅ Làm tròn timestamp theo 10 phút để tránh cache tràn
    try:
        rounded_ts = int(int(timestamp) / 1200) * 1200  # làm tròn về 10 phút
    except Exception:
        rounded_ts = int(datetime.datetime.utcnow().timestamp() / 1200) * 1200

    # ✅ Thêm log kiểm tra cache key
    cache_key = f"map:tile:{layer}:{rounded_ts}:{z}:{x}:{y}"
    # logger.info(f"[CACHE-DEBUG] Checking Redis key = {cache_key}")

    cached = cache.get(cache_key)
    if cached:
        try:
            ttl = cache.ttl(cache_key)
            # logger.info(f"[CACHE-DEBUG] ✅ HIT cache! TTL = {ttl}s")
            content = cached.get("content")
            content_type = cached.get("content_type", "image/png")
            logger.debug("✅ Trả tile từ Redis cache key=%s", cache_key)
            resp = HttpResponse(content, content_type=content_type)
            resp["X-Cache"] = "HIT"
            return resp
        except Exception:
            logger.exception("proxy_tile: failed to return cached tile, refetching")
    # else:
    #     logger.info("[CACHE-DEBUG] ❌ MISS cache! Creating new entry...")

    # base parameters
    params = {
        "date": timestamp,  # ⚠️ vẫn dùng timestamp thật để API đúng thời điểm
        "appid": OPENWEATHER_API_KEY,
    }

    # 🎨 custom palette riêng cho Temperature (TA2)
    if layer == "temp":
        params.update({
            "opacity": "0.6",
            "fill_bound": "true",
            "palette": "-65:821692;-55:821692;-45:821692;-40:821692;-30:8257DB;"
                       "-20:208CEC;-10:20C4E8;0:23DDDD;10:C2FF28;20:FFF028;"
                       "25:FFC228;30:FC8014"
        })
    else:
        params.update({
            "opacity": "0.9",
            "fill_bound": "true"
        })

    layer_code = layer_map[layer]
    tile_url = f"https://maps.openweathermap.org/maps/2.0/weather/{layer_code}/{z}/{x}/{y}?{urlencode(params)}"
    # logger.info("proxy_tile: fetching from OpenWeather v2.0 => %s", tile_url)

    try:
        r = requests.get(tile_url, timeout=10)
    except Exception as e:
        logger.exception("proxy_tile: OpenWeather 2.0 request failed")
        return Response({"error": "Failed to fetch tile", "details": str(e)}, status=502)

    if r.status_code != 200:
        logger.warning("proxy_tile: upstream returned %s for %s", r.status_code, tile_url)
        return Response({"error": "Upstream tile error", "status_code": r.status_code, "text": r.text}, status=502)

    content = r.content
    content_type = r.headers.get("Content-Type", "image/png")

    try:
        cache.set(cache_key, {"content": content, "content_type": content_type}, timeout=TILE_CACHE_TIMEOUT)
        logger.info(f"[CACHE-DEBUG] 🔁 Lưu tile vào Redis cache key = {cache_key}")
    except Exception:
        logger.exception("proxy_tile: Không lưu được tile vào cache")

    resp = HttpResponse(content, content_type=content_type)
    resp["X-Cache"] = "MISS"
    return resp
