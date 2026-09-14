from flask import Flask, render_template, request
import requests
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("OPENWEATHER_API_KEY")


@app.route("/", methods=["GET", "POST"])
def home():

    weather = None
    forecast = None
    error = None

    if request.method == "POST":

        city = request.form.get("city", "").strip()

        if not city:
            error = "Please enter a city name."

        elif not API_KEY:
            error = "API key is missing. Please check your .env file."

        else:

            weather_url = (
                "https://api.openweathermap.org/data/2.5/weather"
                f"?q={city}&appid={API_KEY}&units=metric"
            )

            forecast_url = (
                "https://api.openweathermap.org/data/2.5/forecast"
                f"?q={city}&appid={API_KEY}&units=metric"
            )

            try:

                weather_response = requests.get(
                    weather_url,
                    timeout=10
                )

                forecast_response = requests.get(
                    forecast_url,
                    timeout=10
                )

                # ---------------- CURRENT WEATHER ----------------

                if weather_response.status_code == 200:

                    weather_data = weather_response.json()

                    weather = {
                        "city": weather_data["name"],
                        "country": weather_data["sys"]["country"],
                        "temperature": round(
                            weather_data["main"]["temp"]
                        ),
                        "feels_like": round(
                            weather_data["main"]["feels_like"]
                        ),
                        "humidity": weather_data["main"]["humidity"],
                        "description": weather_data["weather"][0][
                            "description"
                        ].title(),
                        "wind": weather_data["wind"]["speed"],
                    }

                elif weather_response.status_code == 401:

                    error = "API key is invalid or not activated yet."

                elif weather_response.status_code == 404:

                    error = (
                        "City not found. "
                        "Please enter a valid city name."
                    )

                else:

                    error = (
                        "Unable to fetch weather data. "
                        "Please try again."
                    )

                # ---------------- 5 DAY FORECAST ----------------

                if (
                    weather_response.status_code == 200
                    and forecast_response.status_code == 200
                ):

                    forecast_data = forecast_response.json()

                    daily_data = {}

                    for item in forecast_data["list"]:

                        date_time = datetime.fromtimestamp(
                            item["dt"]
                        )

                        date_key = date_time.strftime("%Y-%m-%d")

                        hour = date_time.hour

                        # Calculate how close the forecast is to 12 PM
                        difference = abs(hour - 12)

                        if (
                            date_key not in daily_data
                            or difference
                            < daily_data[date_key]["difference"]
                        ):

                            daily_data[date_key] = {

                                "difference": difference,

                                "date": date_time.strftime(
                                    "%d %b"
                                ),

                                "day": date_time.strftime(
                                    "%A"
                                ),

                                "temperature": round(
                                    item["main"]["temp"]
                                ),

                                "description": item["weather"][0][
                                    "description"
                                ].title(),

                                "humidity": item["main"]["humidity"],

                                "wind": item["wind"]["speed"],
                            }

                    # Remove today's data if present
                    forecast_list = list(
                        daily_data.values()
                    )

                    # Sort by date
                    forecast_list.sort(
                        key=lambda x: datetime.strptime(
                            x["date"],
                            "%d %b"
                        )
                    )

                    forecast = forecast_list[:5]

                elif weather_response.status_code == 200:

                    error = (
                        "Current weather loaded, "
                        "but forecast could not be loaded."
                    )

            except requests.exceptions.RequestException:

                error = (
                    "Could not connect to the weather service."
                )

    return render_template(
        "index.html",
        weather=weather,
        forecast=forecast,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)