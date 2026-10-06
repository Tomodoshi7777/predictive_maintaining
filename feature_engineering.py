import math

import pandas as pd


REQUIRED_INPUTS = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
    "Type",
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create the same engineered features used during model training."""

    data = df.copy()

    # Validate required inputs
    missing = [col for col in REQUIRED_INPUTS if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Validate machine type
    valid_types = {"H", "L", "M"}
    invalid_types = set(data["Type"].dropna().unique()) - valid_types

    if invalid_types:
        raise ValueError(
            f"Invalid Type values: {sorted(invalid_types)}. "
            f"Expected: H, L, or M."
        )

    # One-hot encode Type
    type_dummies = pd.get_dummies(
        data["Type"],
        prefix="Type",
        dtype=int,
    )

    for column in ["Type_H", "Type_L", "Type_M"]:
        if column not in type_dummies:
            type_dummies[column] = 0

    type_dummies = type_dummies[["Type_H", "Type_L", "Type_M"]]

    data = pd.concat(
        [data.drop(columns=["Type"]), type_dummies],
        axis=1,
    )

    # Temperature difference
    data["temp_diff_k"] = (
        data["Process temperature [K]"]
        - data["Air temperature [K]"]
    )

    # Mechanical power
    data["power_w"] = (
        data["Torque [Nm]"]
        * data["Rotational speed [rpm]"]
        * 2
        * math.pi
        / 60
    )

    # Tool wear × torque
    data["tool_wear_x_torque"] = (
        data["Tool wear [min]"]
        * data["Torque [Nm]"]
    )

    # Tool wear risk tier
    def get_risk_tier(wear):
        if wear < 50:
            return 0
        elif wear < 100:
            return 1
        elif wear < 150:
            return 2
        elif wear < 200:
            return 3
        return 4

    data["risk_tier"] = data["Tool wear [min]"].apply(get_risk_tier)

    # HDF risk condition
    data["hdf_risk_flag"] = (
        (data["temp_diff_k"] < 8.6)
        & (data["Rotational speed [rpm]"] < 1380)
    ).astype(int)

    # Power category
    def get_power_category(power):
        if power < 3500:
            return "LOW"
        elif power > 9000:
            return "HIGH"
        return "NORMAL"

    data["power_category"] = data["power_w"].apply(get_power_category)

    # Strain
    data["strain"] = (
        data["Tool wear [min]"]
        * data["Torque [Nm]"]
        / (data["Rotational speed [rpm]"] + 1)
    )

    # Temperature ratio
    data["temp_ratio"] = (
        data["Process temperature [K]"]
        / data["Air temperature [K]"]
    )

    # Power per RPM
    data["power_per_rpm"] = (
        data["power_w"]
        / (data["Rotational speed [rpm]"] + 1)
    )

    # Wear per RPM
    data["wear_per_rpm"] = (
        data["Tool wear [min]"]
        / (data["Rotational speed [rpm]"] + 1)
    )

    # One-hot encode power category
    power_dummies = pd.get_dummies(
        data["power_category"],
        prefix="power",
        dtype=int,
    )

    for column in ["power_HIGH", "power_LOW", "power_NORMAL"]:
        if column not in power_dummies:
            power_dummies[column] = 0

    power_dummies = power_dummies[
        ["power_HIGH", "power_LOW", "power_NORMAL"]
    ]

    data = pd.concat(
        [
            data.drop(columns=["power_category"]),
            power_dummies,
        ],
        axis=1,
    )

    return data