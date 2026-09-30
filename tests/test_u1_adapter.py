"""Focused tests for the Snapmaker U1 compatibility layer."""

from __future__ import annotations

import pytest

from chopper_tune import ChopperTune, MeasurementMode


class FakeGCode:
    def __init__(self):
        self.messages = []

    def respond_info(self, message):
        self.messages.append(message)


class FakePrinter:
    def __init__(self, objects=None):
        self.objects = objects or {}

    def lookup_object(self, name, default=None):
        return self.objects.get(name, default)

    @staticmethod
    def command_error(message):
        return RuntimeError(message)


class SampleSensor:
    name = "e0_lis2dw"

    @staticmethod
    def start_internal_client():
        return object()


def make_tuner(objects=None):
    tuner = ChopperTune.__new__(ChopperTune)
    tuner.printer = FakePrinter(objects)
    tuner.gcode = FakeGCode()
    return tuner


def test_resolves_firmware_16_sensor_selector():
    sensor = SampleSensor()
    selector = type("Selector", (), {"sensor_identified": sensor})()
    tuner = make_tuner(
        {"sensor_accelerometer_identify e0_accelerometer": selector}
    )

    name, resolved = tuner.resolve_accelerometer(
        "sensor_accelerometer_identify e0_accelerometer"
    )

    assert name == "e0_lis2dw"
    assert resolved is sensor


def test_resolves_legacy_direct_sensor():
    sensor = SampleSensor()
    tuner = make_tuner({"lis2dw e0_lis2dw": sensor})

    name, resolved = tuner.resolve_accelerometer("lis2dw e0_lis2dw")

    assert name == "e0_lis2dw"
    assert resolved is sensor


def test_unidentified_selector_has_actionable_error():
    selector = type("Selector", (), {"sensor_identified": None})()
    tuner = make_tuner(
        {"sensor_accelerometer_identify e0_accelerometer": selector}
    )

    with pytest.raises(RuntimeError, match="Dock toolhead 0"):
        tuner.resolve_accelerometer(
            "sensor_accelerometer_identify e0_accelerometer"
        )


def test_u1_rejects_z_and_non_corexy():
    tuner = make_tuner()
    tuner.kinematics = "corexy"
    with pytest.raises(RuntimeError, match="AXIS=X or AXIS=Y only"):
        tuner.get_axes_and_steppers("z")

    tuner.kinematics = "cartesian"
    with pytest.raises(RuntimeError, match="requires CoreXY"):
        tuner.get_axes_and_steppers("x")


def test_auto_speed_keeps_boundary_margin():
    tuner = make_tuner()
    tuner.measurement_mode = MeasurementMode.Resonances
    tuner.debug = False
    tuner.required_rpm = (37.5, 150.0, 1.5)
    tuner.boundary_margin = 1.0
    tuner.settings = {"printer": {"max_velocity": 500.0}}
    tuner.stepper_settings = {
        "stepper_x": {
            "rotation_distance": 40.0,
            "full_steps_per_rotation": 400,
        }
    }

    minimum, maximum, step = tuner.configure_speed_limits(
        min_speed=None,
        max_speed=None,
        speed_change_step=None,
        measure_time=1.25,
        axes=("x", "y"),
        steppers=("stepper_x", "stepper_y"),
        a_axis_min=10.0,
        a_axis_max=261.0,
        acceleration=20000.0,
    )
    distance = tuner.calculate_travel_distance(
        axes=("x", "y"),
        a_axis_min=10.0,
        a_axis_max=261.0,
        max_speed=maximum,
        acceleration=20000.0,
        measure_time=1.25,
        travel_distance=None,
    )

    assert minimum > 0
    assert step > 0
    assert distance <= 250.0
