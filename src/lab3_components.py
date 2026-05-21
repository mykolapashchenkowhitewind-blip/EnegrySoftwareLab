from dataclasses import dataclass


@dataclass
class SolarPV:
    capacity_kw: float
    efficiency_factor: float = 0.92
    degradation_factor: float = 0.985
    temperature_coefficient: float = -0.004
    reference_temperature_c: float = 25.0

    def generation(self, irradiation_w_m2: float, temperature_c: float) -> float:
        irradiance_factor = max(0.0, irradiation_w_m2) / 1000.0
        temperature_factor = 1.0 + self.temperature_coefficient * (temperature_c - self.reference_temperature_c)
        generation_kwh = self.capacity_kw * irradiance_factor * self.efficiency_factor * self.degradation_factor * temperature_factor
        return max(0.0, generation_kwh)


@dataclass
class Battery:
    capacity_kwh: float
    max_charge_kw: float
    max_discharge_kw: float
    charge_efficiency: float = 0.94
    discharge_efficiency: float = 0.94
    min_soc_percent: float = 20.0
    max_soc_percent: float = 90.0
    initial_soc_percent: float = 50.0
    self_discharge_percent_per_hour: float = 0.01

    def __post_init__(self) -> None:
        self.energy_kwh = self.capacity_kwh * self.initial_soc_percent / 100.0

    @property
    def min_energy_kwh(self) -> float:
        return self.capacity_kwh * self.min_soc_percent / 100.0

    @property
    def max_energy_kwh(self) -> float:
        return self.capacity_kwh * self.max_soc_percent / 100.0

    @property
    def soc_percent(self) -> float:
        return self.energy_kwh / self.capacity_kwh * 100.0

    def charge(self, available_energy_kwh: float) -> float:
        if available_energy_kwh <= 0:
            return 0.0
        accepted_from_source = min(available_energy_kwh, self.max_charge_kw)
        remaining_capacity = self.max_energy_kwh - self.energy_kwh
        accepted_from_source = min(accepted_from_source, remaining_capacity / self.charge_efficiency)
        stored = accepted_from_source * self.charge_efficiency
        self.energy_kwh += stored
        return max(0.0, accepted_from_source)

    def discharge(self, required_energy_kwh: float) -> float:
        if required_energy_kwh <= 0:
            return 0.0
        available_to_load = (self.energy_kwh - self.min_energy_kwh) * self.discharge_efficiency
        delivered = min(required_energy_kwh, self.max_discharge_kw, available_to_load)
        self.energy_kwh -= delivered / self.discharge_efficiency
        return max(0.0, delivered)

    def apply_self_discharge(self) -> None:
        loss = self.capacity_kwh * self.self_discharge_percent_per_hour / 100.0
        self.energy_kwh = max(self.min_energy_kwh, self.energy_kwh - loss)


@dataclass
class Grid:
    import_limit_kw: float
    export_limit_kw: float
    export_price_uah_per_kwh: float = 6.5

    def import_energy(self, required_energy_kwh: float) -> float:
        return max(0.0, min(required_energy_kwh, self.import_limit_kw))

    def export_energy(self, surplus_energy_kwh: float) -> float:
        return max(0.0, min(surplus_energy_kwh, self.export_limit_kw))

    def import_cost(self, imported_kwh: float, tariff_price_uah_per_kwh: float) -> float:
        return imported_kwh * tariff_price_uah_per_kwh

    def export_revenue(self, exported_kwh: float) -> float:
        return exported_kwh * self.export_price_uah_per_kwh
