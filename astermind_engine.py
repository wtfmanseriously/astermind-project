import time
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class StreamPacket:
    source_arm: int
    timestamp: float
    data: np.ndarray

class ExtremeLearningMachine:
    def __init__(self, input_dim: int, hidden_dim: int = 16):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.w_in = np.random.normal(0, 0.5, (input_dim, hidden_dim))
        self.bias = np.random.normal(0, 0.1, (hidden_dim,))
        self.beta = np.zeros((hidden_dim, 1))

    def _activate(self, X: np.ndarray) -> np.ndarray:
        return np.maximum(0, np.dot(X, self.w_in) + self.bias)

    def fit(self, X: np.ndarray, y: np.ndarray):
        H = self._activate(X)
        reg = 1e-3 * np.eye(self.hidden_dim)
        self.beta = np.dot(np.linalg.pinv(np.dot(H.T, H) + reg), np.dot(H.T, y))

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.dot(self._activate(X), self.beta)


class MechanicallyCoupledArm:
    """
    Decentralized arm with lateral mechanical coupling to neighboring radial limbs.
    Simulates the bio-mechanical coordination of starfish peripheral nerve rings.
    """
    def __init__(self, arm_id: int, input_dim: int = 4):
        self.arm_id = arm_id
        # Input dim + 2 for lateral neighbor inputs (left and right adjacent arms)
        self.elm = ExtremeLearningMachine(input_dim=input_dim + 2, hidden_dim=12)
        self.membrane_potential = 0.0
        self.decay = 0.65
        self.threshold = 1.2
        self.refractory_steps = 0
        self.last_state_output = 0.0

        dummy_x = np.random.normal(0, 1, (25, input_dim + 2))
        dummy_y = np.linalg.norm(dummy_x, axis=1, keepdims=True)
        self.elm.fit(dummy_x, dummy_y)

    def step(self, raw_features: np.ndarray, left_neighbor_val: float, right_neighbor_val: float) -> Dict[str, Any]:
        # Fuses local sensor vector with neighboring arm dynamics
        coupled_vector = np.concatenate([raw_features, [left_neighbor_val, right_neighbor_val]])
        prediction = float(self.elm.predict(coupled_vector.reshape(1, -1))[0, 0])
        self.last_state_output = prediction

        if self.refractory_steps > 0:
            self.refractory_steps -= 1
            spiked = False
        else:
            self.membrane_potential = (self.membrane_potential * self.decay) + abs(prediction)
            if self.membrane_potential >= self.threshold:
                spiked = True
                self.membrane_potential = 0.0
                self.refractory_steps = 2
            else:
                spiked = False

        return {"arm_id": self.arm_id, "spiked": spiked, "representation": prediction}


class RadialStarfishNetwork:
    """Complete AsterMind Core: Lateral Ring Coupling + EVO Classifier + Gated Core."""
    def __init__(self, num_arms: int = 5, input_dim: int = 4):
        self.num_arms = num_arms
        self.arms = [MechanicallyCoupledArm(i, input_dim) for i in range(num_arms)]
        self.system_stability: float = 1.0
        self.w_evo = np.random.uniform(0.3, 0.7, size=(num_arms,))
        self.token_savings: int = 0

    def process_cycle(self, sensor_streams: List[StreamPacket]) -> Dict[str, Any]:
        arm_outputs = []
        for i, arm in enumerate(self.arms):
            # Ring topology neighbors: (i-1) and (i+1) modulo N
            left_val = self.arms[(i - 1) % self.num_arms].last_state_output
            right_val = self.arms[(i + 1) % self.num_arms].last_state_output
            res = arm.step(sensor_streams[i].data, left_val, right_val)
            arm_outputs.append(res)

        spikes = [o["arm_id"] for o in arm_outputs if o["spiked"]]
        representations = [o["representation"] for o in arm_outputs]

        # Ring coherence decay
        coactivation_ratio = len(spikes) / max(1, self.num_arms)
        self.system_stability = (0.55 * self.system_stability) + (0.45 * (1.0 - coactivation_ratio))

        # Real-time state classification
        aggregated_energy = float(np.dot(self.w_evo, np.abs(representations)))
        if self.system_stability < 0.65 or aggregated_energy > 3.0:
            state = "Critical Disruption"
        elif self.system_stability < 0.85 or aggregated_energy > 1.5:
            state = "Telemetry Drift"
        else:
            state = "Nominal Equilibrium"

        escalate = self.system_stability < 0.70
        if not escalate:
            self.token_savings += 1

        return {
            "spikes": spikes,
            "stability": round(self.system_stability, 3),
            "state": state,
            "escalated": escalate
        }


if __name__ == "__main__":
    np.random.seed(42)
    network = RadialStarfishNetwork(num_arms=5, input_dim=4)

    print("AsterMind Coupled Radial Network running in real-time...")
    print("Press Ctrl + C in terminal to stop streaming.\n")
    print(f"{'Cycle':<8}{'Stability':<12}{'Spikes':<18}{'EVO State':<22}{'Action'}")
    print("-" * 75)

    try:
        for t in range(1, 21):
            # Introduce a temporary anomaly burst between cycles 8 and 12
            is_anomaly = 8 <= t <= 12
            scale = 1.8 if is_anomaly else 0.08
            noise = np.random.uniform(1.0, 2.5, 4) if is_anomaly else np.random.normal(0.05, 0.02, 4)

            packets = [
                StreamPacket(source_arm=i, timestamp=time.time(), data=noise)
                for i in range(5)
            ]

            out = network.process_cycle(packets)
            action = "[LLM ESCALATION]" if out["escalated"] else "[Local 0-Token]"
            
            print(f"{t:<8}{out['stability']:<12}{str(out['spikes']):<18}{out['state']:<22}{action}")
            time.sleep(0.3)  # Streaming delay

    except KeyboardInterrupt:
        pass

    print("-" * 75)
    print(f"Streaming run complete. Total routine cycles resolved locally: {network.token_savings}")

