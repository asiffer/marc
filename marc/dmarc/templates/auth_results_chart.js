{% load dmarc_extras %}
new Chart(document.getElementById("{{ id }}").getContext("2d"), {
  type: "doughnut",
  data: {
    labels: {{ labels|jsonify }},
    datasets: [
      {
        data: {{ data|jsonify }},
        hoverOffset: 4,
        backgroundColor: {{ background_colors|jsonify }}
      },
    ],
  },
  options: {
    plugins: {
      legend : {
        display: false,
      }
    }
  }
});
