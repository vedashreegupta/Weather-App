import customtkinter as ctk
import requests

# Set theme and color style
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def get_weather():
    city = city_entry.get().strip()
    
    if not city:
        result_label.configure(text="⚠️ Please enter a city name!", text_color="orange")
        return
    
    result_label.configure(text="⏳ Fetching weather...", text_color="gray")
    app.update()
    
    # Using wttr.in for free, keyless weather data
    url = f"https://wttr.in/{city}?format=j1"
    
    try:
        response = requests.get(url, timeout=7)
        if response.status_code != 200:
            result_label.configure(text="❌ City not found. Please check spelling.", text_color="#FF6B6B")
            return
            
        data = response.json()
        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        condition = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        wind = current["windspeedKmph"]
        feels_like = current["FeelsLikeC"]
        
        # Display formatted weather results
        result_label.configure(
            text=f"📍 {city.title()}\n\n"
                 f"🌡️ Temperature: {temp_c}°C\n"
                 f"🤔 Feels Like: {feels_like}°C\n"
                 f"☁️ Condition: {condition}\n"
                 f"💧 Humidity: {humidity}%\n"
                 f"💨 Wind: {wind} km/h",
            text_color="#E0E0E0"
        )
    except Exception as e:
        result_label.configure(text="❌ Network error. Check connection!", text_color="#FF6B6B")

# --- Initialize Desktop App ---
app = ctk.CTk()
app.title("Modern Weather App")
app.geometry("400x500")
app.resizable(False, False)

# App Title
title_label = ctk.CTkLabel(app, text="🌤️ Weather App", font=("Arial", 26, "bold"))
title_label.pack(pady=(30, 10))

# Subtitle
sub_label = ctk.CTkLabel(app, text="Enter a city to get real-time weather", font=("Arial", 13), text_color="gray")
sub_label.pack(pady=(0, 20))

# City Input Field
city_entry = ctk.CTkEntry(app, placeholder_text="e.g. New York, London, Tokyo", width=280, height=40, font=("Arial", 14))
city_entry.pack(pady=10)
city_entry.bind("<Return>", lambda event: get_weather())

# Search Button
search_btn = ctk.CTkButton(app, text="Check Weather", width=280, height=40, font=("Arial", 15, "bold"), command=get_weather)
search_btn.pack(pady=15)

# Card frame for displaying weather results
card_frame = ctk.CTkFrame(app, width=320, height=220, corner_radius=12)
card_frame.pack(pady=15, padx=20, fill="both", expand=True)

result_label = ctk.CTkLabel(card_frame, text="Search for a city above 👆", font=("Arial", 15), justify="center")
result_label.place(relx=0.5, rely=0.5, anchor="center")

# Run the app window
if __name__ == "__main__":
    app.mainloop()
