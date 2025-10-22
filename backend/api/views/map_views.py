import requests
import datetime
import logging
from urllib.parse import urlencode
from django.http import HttpResponse
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# CONFIG
OPENWEATHER_API_KEY = "49d2545d1cdff8820a039e6e2f451ffc"  # lưu backend, không cho frontend thấy
METADATA_CACHE_TIMEOUT = 300  # 5 phút
TILE_CACHE_TIMEOUT = 300      # 5 phút (cache bytes)
MAX_TIMESTAMP_RANGE_HOURS = 48


@api_view(["GET"])
@permission_classes([AllowAny])
def get_weather_map(request):
    """
    Trả metadata cho frontend — xác định endpoint tile proxy và timestamps cho timelapse.
    """
    layer = (request.GET.get("layer") or "wind").lower()
    hours = int(request.GET.get("hours") or 24)
    interval_h = int(request.GET.get("interval_h") or 3)

    if hours < 1:
        hours = 24
    if hours > MAX_TIMESTAMP_RANGE_HOURS:
        hours = MAX_TIMESTAMP_RANGE_HOURS
    if interval_h < 1:
        interval_h = 1

    # Map giữa tên frontend và OpenWeather 2.0 layer ID
    layer_map = {
        "clouds": "CL",
        "temp": "TA2",
        "wind": "WND",
        "precipitation": "PR0",
    }

    if layer not in layer_map:
        logger.debug("get_weather_map: invalid layer requested: %s", layer)
        return Response({"error": "Invalid layer name"}, status=400)

    # Tạo timestamps (hiện tại + 24h tới, mỗi 3h)
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

    legend_map = {
        "temp": "https://openweathermap.org/themes/openweathermap/assets/vendor/owm/img/widgets/temp_c_scale.png",
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
    layer = (request.GET.get("layer") or "wind").lower()
    z = request.GET.get("z")
    x = request.GET.get("x")
    y = request.GET.get("y")
    timestamp = request.GET.get("timestamp")

    if not all([z, x, y]):
        return Response({"error": "Missing tile coordinates (z,x,y)."}, status=400)

    layer_map = {
        "clouds": "CL",
        "temp": "TA2",
        "wind": "WND",
        "precipitation": "PR0"
    }

    if layer not in layer_map:
        return Response({"error": "Invalid layer name"}, status=400)

    if not timestamp:
        timestamp = str(int(datetime.datetime.utcnow().timestamp()))

    cache_key = f"map:tile:{layer}:{timestamp}:{z}:{x}:{y}"
    cached = cache.get(cache_key)
    if cached:
        try:
            content = cached.get("content")
            content_type = cached.get("content_type", "image/png")
            resp = HttpResponse(content, content_type=content_type)
            resp["X-Cache"] = "HIT"
            return resp
        except Exception:
            logger.exception("proxy_tile: failed to return cached tile, refetching")

    # 🔹 Dùng API 2.0: https://maps.openweathermap.org/maps/2.0/weather/{layer}/{z}/{x}/{y}
    params = {
        "date": timestamp,
        "opacity": "0.9",
        "fill_bound": "true",
        "appid": OPENWEATHER_API_KEY
    }

    layer_code = layer_map[layer]
    tile_url = f"https://maps.openweathermap.org/maps/2.0/weather/{layer_code}/{z}/{x}/{y}?{urlencode(params)}"

    logger.info("proxy_tile: fetching from OpenWeather v2.0 => %s", tile_url)

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

    cache.set(cache_key, {"content": content, "content_type": content_type}, timeout=TILE_CACHE_TIMEOUT)
    resp = HttpResponse(content, content_type=content_type)
    resp["X-Cache"] = "MISS"
    return resp
