# Parametric Geometry App 🏙️

Dive into the world of parametric design with the Parametric Geometry App! Harness the power of [Ladybug tools](https://www.ladybug.tools/) and [Streamlit](https://streamlit.io/) to quickly craft your ideal building, all based on a few simple parameters.

<img src="img\gif_demo.gif">

# Features 🌟

## Interactive Design Interface

Adjust building parameters such as footprint, floor height, and number of floors through user-friendly sliders and input fields. This immediate interaction allows for a dynamic exploration of architectural possibilities. If you have an existing `HBJSON` model, just upload it directly!

## Dynamic 3D Visualization

Our app employs Honeybee and Ladybug for 3D visualization, providing a real-time view of your building model as parameters are modified. This immersive experience helps in understanding spatial relationships and design impacts.

## Comprehensive HVAC Modelling

The app supports a broad spectrum of HVAC system configurations, enabling detailed analysis of their influence on building comfort and energy efficiency. Users can explore and customize various HVAC types, including:

- **All-Air Systems**: Choose from PSZ, VAV, PVAV, and more, suitable for different building sizes and types.
- **Radiant Systems**: Including radiant floors and ceilings, these options offer comfort and efficiency by directly heating or cooling building occupants.
- **DOAS (Dedicated Outdoor Air Systems)**: Integrated with other HVAC components, DOAS ensures fresh air supply, improving indoor air quality.
- **Hybrid Systems**: Combining the benefits of multiple system types to achieve optimal environmental control and energy usage.

Each HVAC option is customizable, allowing for adjustments in efficiency, control types, and integration with renewable energy sources.

## Ultra frast EnergyPlus simulation for a wide number of geographic locations

Quickly run simulation results using the powerful EnergyPlus engine in the back end. Explore annual loads per month and per room.

Download the weather data (EPW and DDY) from [EPW Map](https://www.ladybug.tools/epwmap/) by providing the URL of the requested station. It is all free!

# How it Works 🛠️

User Input: Define your building parameters through the sliders.
Building Generation: The application generates a 3D model based on your inputs.
3D Visualization: Visualize your design in rich 3D, powered by VTK.

# Getting Started 🚀

- Make sure you have Python `3.7` or a more recent version.
- Optionally, create a python virtual environment.
- Install the required libraries. `pip install -r app/requirements.txt`
- To launch the Streamlit application use `streamlit run app/app.py`
- Start playing!

# Contributing 🤝

Feel free to fork, improve, make pull requests or fill issues. I'd love to hear your feedback!

# License

MIT License
