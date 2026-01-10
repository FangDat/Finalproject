<template>
  <div v-if="points && points.length" class="sparkline-wrapper">
    <apexchart
      :key="chartKey"
      type="line"
      height="140"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>

<script>
export default {
  name: "SparklineChart",
  props: {
    points: {
      type: Array,
      required: true,
    },
    direction: {
      type: String,
      default: "flat",
    },
    avgValue: {
      type: String,
      default: "",
    },
    unit: {
      type: String,
      default: "",
    },
      // ⭐ NEW
    valueFormatter: {
        type: Function,
        default: null,
    },
  },
  computed: {
    series() {
      return [
        {
          name: "Value",
          data: this.points.map((p) => p.value),
        },
      ];
    },

    chartOptions() {
      const colors = {
        up: "#ff6b6b",
        down: "#4ecdc4",
        flat: "#95afc0",
      };

      const color = colors[this.direction] || colors.flat;

      return {
        chart: {
          type: "line",
          sparkline: {
            enabled: true,
          },
          toolbar: {
            show: false,
          },
          animations: {
            enabled: false,
          },
          zoom: {
            enabled: false,
          },
        },
        stroke: {
          curve: "smooth",
          width: 3,
          lineCap: "round",
        },
        colors: [color],
        dataLabels: {
          enabled: false,
        },
        tooltip: {
          enabled: true,
          shared: true,
          followCursor: true,
          intersect: false,
          x: {
            show: true,
            formatter: (val, opts) => {
              const point = this.points[opts.dataPointIndex];
              return "🕐 " + (point?.time || "");
            },
          },
            y: {
            formatter: (val) => {
                if (this.valueFormatter) {
                return this.valueFormatter(val);
                }
                return val.toFixed(1) + (this.unit || "");
            },
            title: {
              formatter: () => "",
            },
          },
          marker: {
            show: true,
          },
          style: {
            fontSize: "13px",
            fontWeight: 600,
          },
          theme: "light",
        },
        markers: {
          size: 4,
          colors: [color],
          strokeColors: "#fff",
          strokeWidth: 1,
          hover: {
            size: 5,
          },
        },
        xaxis: {
          categories: this.points.map((p) => this.formatTime(p.time)),
          labels: {
            show: true,
            rotate: 0,
            style: {
              fontSize: "15px",
              fontWeight: 700,
              colors: "rgba(0,0,0,0.6)",
            },
            offsetY: 0,
          },
          axisBorder: {
            show: false,
          },
          axisTicks: {
            show: false,
          },
          tooltip: {
            enabled: false,
          },
        },
        yaxis: {
          show: false,
        },
        grid: {
          show: true,
          borderColor: "rgba(0,0,0,0.05)",
          strokeDashArray: 5,
          position: "back",
          xaxis: {
            lines: {
              show: false,
            },
          },
          yaxis: {
            lines: {
              show: true,
            },
          },
          padding: {
            top: 15,
            right: 10,
            bottom: 5,
            left: 10,
          },
        },
        annotations: {
          yaxis: [
            {
              y: this.avgNormalized,
              borderColor: color,
              strokeDashArray: 6,
              opacity: 0.65,
              borderWidth: 2,
              label: {
                borderColor: "transparent",
                style: {
                  color: "#fff",
                  background: color,
                  fontSize: "13px",
                  fontWeight: 800,
                  padding: {
                    left: 8,
                    right: 8,
                    top: 3,
                    bottom: 3,
                  },
                  borderRadius: 5,
                },
                text: "Avg " + this.avgValue,
                position: "left",
                offsetX: 0,
                offsetY: 0,
              },
            },
          ],
          //xaxis: this.getTimeMarkers(color),
        },
      };
    },

    avgNormalized() {
      if (!this.points?.length) return 0;
      const sum = this.points.reduce((acc, p) => acc + p.value, 0);
      return sum / this.points.length;
    },

    chartKey() {
      return `${this.points.length}-${this.direction}-${this.avgValue}`;
    },
  },
  methods: {
    formatTime(time) {
      if (!time) return "";
      const hour = time.split(":")[0];
      return hour;
    },

    // getTimeMarkers(color) {
    //   const markers = [];
    //   const currentHour = new Date().getHours();

    //   this.points.forEach((point, index) => {
    //     const hour = parseInt(point.time?.split(":")[0] || "0");

    //     if (hour === currentHour && index === 0) {
    //       markers.push({
    //         x: this.formatTime(point.time),
    //         borderColor: "#5f27cd",
    //         strokeDashArray: 0,
    //         borderWidth: 2,
    //         opacity: 0.5,
    //         label: {
    //           style: {
    //             color: "#fff",
    //             background: "#5f27cd",
    //             fontSize: "8px",
    //             fontWeight: 700,
    //             padding: {
    //               left: 5,
    //               right: 5,
    //               top: 1,
    //               bottom: 1,
    //             },
    //             borderRadius: 3,
    //           },
    //           text: "Now",
    //           orientation: "horizontal",
    //           offsetY: -8,
    //         },
    //       });
    //     }
    //   });

    //   return markers;
    // },
  },
};
</script>

<style scoped>
.sparkline-wrapper {
  width: 100%;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-top: 8px;
}

.sparkline-wrapper >>> .apexcharts-canvas {
  overflow: visible !important;
}

.sparkline-wrapper >>> svg {
  overflow: visible !important;
}

.sparkline-wrapper >>> .apexcharts-annotations {
  overflow: visible !important;
}
</style>