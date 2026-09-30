import time
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class SensorReading:
    source_arm_id: int
    timestamp: float
    features: np.ndarray

class RadialArmNode:
    def __init__(self, arm_id: int, input_dim: int, decay: float = 0.9, threshold: float = 1.0):
        self.arm_id = arm_id
        self.weights = np.random.uniform(0.1, 0.5, size=(input_dim,))
        self.voltage = 0.0
        self.decay = decay
        self.threshold = threshold
        self.refractory_count = 0

    def step(self, features: np.ndarray) -> bool:
        if self.refractory_count > 0:
            self.refractory_count -= 1
            return False

        current_input = float(np.dot(self.weights, features))
        self.voltage = (self.voltage * self.decay) + current_input

        if self.voltage >= self.threshold:
            self.voltage = 0.0
            self.refractory_count = 2
            return True
        return False

class CentralDiscCoordinator:
    def __init__(self, num_arms: int, stability_decay: float = 0.5):
        self.num_arms = num_arms
        self.stability_decay = stability_decay
        self.coactivation_history: List[int] = []
        self.stability_index: float = 1.0

    def fuse_spikes(self, active_arm_ids: List[int]) -> float:
        num_active = len(active_arm_ids)
        self.coactivation_history.append(num_active)
        if len(self.coactivation_history) > 20:
            self.coactivation_history.pop(0)

        coactivation_ratio = num_active / max(1, self.num_arms)
        instantaneous_stability = 1.0 - coactivation_ratio

        self.stability_index = (
            self.stability_decay * self.stability_index
            + (1.0 - self.stability_decay) * instantaneous_stability
        )
        return self.stability_index

    def requires_llm_intervention(self, threshold: float = 0.70) -> bool:
        return self.stability_index < threshold

class RadialStarfishAI:
    def __init__(self, num_arms: int = 5, input_dim: int = 4):
        self.arms = [RadialArmNode(arm_id=i, input_dim=input_dim) for i in range(num_arms)]
        self.coordinator = CentralDiscCoordinator(num_arms=num_arms, stability_decay=0.5)
        self.call_cost_saved_events: int = 0

    def process_frame(self, readings: List[SensorReading]) -> Dict[str, Any]:
        spikes = []
        for reading in readings:
            arm = self.arms[reading.source_arm_id]
            if arm.step(reading.features):
                spikes.append(arm.arm_id)

        stability = self.coordinator.fuse_spikes(spikes)
        needs_escalation = self.coordinator.requires_llm_intervention()

        escalation_result: Optional[str] = None
        if needs_escalation:
            escalation_result = self._dispatch_llm_reasoning(spikes, stability)
        else:
            self.call_cost_saved_events += 1

        return {
            "spiking_arms": spikes,
            "stability_index": round(stability, 4),
            "escalated_to_llm": needs_escalation,
            "system_verdict": escalation_result or "Operating within continuous equilibrium."
        }

    def _dispatch_llm_reasoning(self, spikes: List[int], stability: float) -> str:
        return (
            f"[LLM INTERVENTION DISPATCHED] Operational stability dropped to {stability:.2f}. "
            f"Cross-arm anomaly detected across nodes {spikes}. Initiating diagnostic prompt."
        )

if __name__ == "__main__":
    np.random.seed(42)
    engine = RadialStarfishAI(num_arms=5, input_dim=4)

    print("--- Phase 1: Baseline Telemetry (No Anomaly) ---")
    for t in range(5):
        readings = [
            SensorReading(source_arm_id=i, timestamp=time.time(), features=np.random.normal(0.1, 0.05, size=4))
            for i in range(5)
        ]
        result = engine.process_frame(readings)
        print(f"Cycle {t+1:02d} | Spikes: {result['spiking_arms']} | Stability: {result['stability_index']} | Escalated: {result['escalated_to_llm']}")

    print("\n--- Phase 2: Multi-Node Data Anomaly Surge ---")
    for t in range(5, 10):
        readings = [
            SensorReading(source_arm_id=i, timestamp=time.time(), features=np.random.uniform(0.9, 1.6, size=4))
            for i in range(5)
        ]
        result = engine.process_frame(readings)
        print(f"Cycle {t+1:02d} | Spikes: {result['spiking_arms']} | Stability: {result['stability_index']} | Action: {result['system_verdict']}")

    print(f"\nTotal routine cycles handled locally without LLM cost: {engine.call_cost_saved_events}")

