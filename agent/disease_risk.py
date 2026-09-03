def predict_disease_risk(
    ndvi,
    humidity,
    temperature,
    rainfall
):

    if (
        ndvi < 0.5
        # and humidity > 85
        # and rainfall > 10
    ):

        return {
            "risk": "High",
            "color": "Red",
            "percentage": 90,
            "advice": [
                "Possible fungal infection.",
                "Inspect crop immediately.",
                "Avoid standing water.",
                "Consult agriculture expert."
            ]
        }

    elif (
        ndvi < 0.7
        # and humidity > 70
    ):

        return {
            "risk": "Medium",
            "color": "Orange",
            "percentage": 60,
            "advice": [
                "Inspect crop regularly.",
                "Monitor humidity.",
                "Improve field ventilation."
            ]
        }

    else:

        return {
            "risk": "Low",
            "color": "Green",
            "percentage": 15,
            "advice": [
                "Crop looks healthy.",
                "Continue regular monitoring."
            ]
        }