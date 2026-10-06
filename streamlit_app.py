import sys
from pathlib import Path

import streamlit as st

# Add MLOps modules to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "05_mlops" / "pipelines")
)

from inference import predict
from model_loader import load_metadata


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Predictive Maintenance",
    page_icon="🏭",
    layout="wide",
)


# --------------------------------------------------
# Load metadata
# --------------------------------------------------

metadata = load_metadata()

MODEL_VERSION = metadata.get("model_version", "unknown")
MODEL_NAME = metadata.get("model_name", "unknown")


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("🏭 Industrial Predictive Maintenance")
st.subheader("Machine Health & Failure Prediction Dashboard")

st.markdown(
    """
    Enter the current machine sensor readings to estimate
    the probability of machine failure.
    """
)


# --------------------------------------------------
# Model information
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Model", MODEL_NAME)

with col2:
    st.metric("Version", MODEL_VERSION)

with col3:
    st.metric("Task", "Binary Classification")


st.divider()


# --------------------------------------------------
# Machine inputs
# --------------------------------------------------

st.header("Machine Sensor Inputs")

col1, col2 = st.columns(2)

with col1:

    air_temperature = st.number_input(
        "Air temperature [K]",
        min_value=250.0,
        max_value=400.0,
        value=298.1,
        step=0.1,
    )

    process_temperature = st.number_input(
        "Process temperature [K]",
        min_value=250.0,
        max_value=450.0,
        value=308.6,
        step=0.1,
    )

    rotational_speed = st.number_input(
        "Rotational speed [rpm]",
        min_value=500,
        max_value=5000,
        value=1550,
        step=10,
    )


with col2:

    torque = st.number_input(
        "Torque [Nm]",
        min_value=0.0,
        max_value=200.0,
        value=42.8,
        step=0.1,
    )

    tool_wear = st.number_input(
        "Tool wear [min]",
        min_value=0,
        max_value=300,
        value=120,
        step=1,
    )

    machine_type = st.selectbox(
        "Machine Type",
        options=["L", "M", "H"],
        index=1,
    )


# --------------------------------------------------
# Prediction
# --------------------------------------------------

st.divider()

if st.button(
    "🔍 Predict Machine Failure",
    type="primary",
    use_container_width=True,
):

    machine_data = {
        "Air temperature [K]": air_temperature,
        "Process temperature [K]": process_temperature,
        "Rotational speed [rpm]": rotational_speed,
        "Torque [Nm]": torque,
        "Tool wear [min]": tool_wear,
        "Type": machine_type,
    }

    try:

        with st.spinner("Running prediction..."):

            result = predict(machine_data)

        st.success("Prediction completed successfully.")

        st.divider()

        # --------------------------------------------------
        # Results
        # --------------------------------------------------

        probability = result["failure_probability"]
        threshold = result["threshold"]
        prediction = result["prediction"]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Failure Probability",
                f"{probability:.2%}",
            )

        with col2:
            st.metric(
                "Decision Threshold",
                f"{threshold:.2%}",
            )

        with col3:

            if prediction == 1:
                st.error("⚠️ FAILURE RISK")
            else:
                st.success("✅ NORMAL")


        # --------------------------------------------------
        # Probability visualization
        # --------------------------------------------------

        st.subheader("Failure Risk")

        st.progress(
            min(max(probability, 0.0), 1.0)
        )

        if prediction == 1:

            st.warning(
                "The predicted failure probability is above "
                "the configured decision threshold."
            )

        else:

            st.info(
                "The predicted failure probability is below "
                "the configured decision threshold."
            )


        # --------------------------------------------------
        # Prediction details
        # --------------------------------------------------

        with st.expander("Prediction Details"):

            st.json(
                {
                    "model": result["model_name"],
                    "model_version": MODEL_VERSION,
                    "prediction": prediction,
                    "failure_probability": probability,
                    "threshold": threshold,
                }
            )

        st.caption(
            "Prediction is automatically logged to the "
            "MLOps prediction history database."
        )

    except Exception as exc:

        st.error(
            "Prediction failed. Please check the application "
            "configuration and database connection."
        )

        st.exception(exc)


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption(
    "TechTrek Graduation Project — Industrial Predictive Maintenance & Failure Prevention"
)