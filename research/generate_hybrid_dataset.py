"""
CivicLens AI — Hybrid Benchmark Dataset Generator & Curator
Generates curated civic infrastructure benchmark samples with ground truth annotations.
"""

import json
import os
import random
from typing import List, Dict, Any

CATEGORIES = [
    ("POTHOLE", "Municipal Roads Department", "HIGH", "P2"),
    ("DAMAGED_ROAD", "Municipal Roads Department", "MEDIUM", "P3"),
    ("STREETLIGHT", "Electrical & Public Lighting Department", "MEDIUM", "P3"),
    ("GARBAGE", "Solid Waste & Sanitation Department", "HIGH", "P2"),
    ("ILLEGAL_DUMPING", "Solid Waste & Sanitation Department", "MEDIUM", "P3"),
    ("DRAINAGE", "Stormwater & Drainage Department", "HIGH", "P2"),
    ("WATER_LEAKAGE", "Water Supply & Sewerage Board", "CRITICAL", "P1"),
    ("DAMAGED_SIGN", "Traffic & Road Safety Cell", "LOW", "P4"),
    ("FOOTPATH", "Civil Infrastructure & Footpath Division", "MEDIUM", "P3"),
    ("OPEN_MANHOLE", "Underground Drainage & Safety Department", "CRITICAL", "P1")
]

SAMPLE_PHRASES = {
    "POTHOLE": [
        "Massive deep crater on the main road",
        "Pothole causing severe vehicle damage and traffic bottleneck",
        "Multiple road depressions after heavy monsoon rains",
        "Dangerous road cavity near pedestrian crossing",
        "Deep asphalt hole right after the turn"
    ],
    "STREETLIGHT": [
        "Streetlight pole completely dark on residential avenue",
        "Blinking and non-functional light creating dark spot",
        "Damaged street lamp fixture after storm",
        "Cluster of 4 street lamps unlit since yesterday",
        "Broken lamp post with exposed casing"
    ],
    "GARBAGE": [
        "Overflowing garbage dumpster blocking sidewalk",
        "Uncollected municipal trash heap attracting stray animals",
        "Foul smell from overflowing waste bin near community center",
        "Rotting food waste and garbage piled up on curb",
        "Commercial market waste dumped outside entrance"
    ],
    "OPEN_MANHOLE": [
        "Open manhole chamber missing concrete cover",
        "Dangerous open sewer pit right in front of school",
        "Broken drain lid with open falling hazard",
        "Missing metal manhole plate on active traffic lane",
        "Uncovered drainage chamber on footpath"
    ],
    "WATER_LEAKAGE": [
        "Drinking water main pipeline burst flooding street",
        "Continuous water supply pipe leakage under tarmac",
        "High pressure water pipe rupture wasting potable water",
        "Clean water gushing from broken underground connection",
        "Water supply line cracked near valve"
    ]
}

def generate_benchmark_dataset(num_samples: int = 250, output_path: str = "research/data/benchmark_dataset.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    dataset = []

    # Base GPS coordinates for Metropolis City (New Delhi area)
    base_lat = 28.6328
    base_lng = 77.2197

    for i in range(num_samples):
        cat_info = random.choice(CATEGORIES)
        cat_code, dept_name, baseline_sev, baseline_prio = cat_info
        
        phrases = SAMPLE_PHRASES.get(cat_code, [f"Reported {cat_code.lower().replace('_', ' ')} incident on local street"])
        description = random.choice(phrases)
        
        # Add random coordinate jitter within 5km radius (~0.045 deg)
        lat_jitter = (random.random() - 0.5) * 0.08
        lng_jitter = (random.random() - 0.5) * 0.08

        sample = {
            "sample_id": f"BENCH-{i+1:04d}",
            "description": description,
            "text": description,
            "ground_truth_category": cat_code,
            "ground_truth_department": dept_name,
            "ground_truth_severity": baseline_sev,
            "ground_truth_priority": baseline_prio,
            "lat": round(base_lat + lat_jitter, 6),
            "lng": round(base_lng + lng_jitter, 6),
            "latitude": round(base_lat + lat_jitter, 6),
            "longitude": round(base_lng + lng_jitter, 6),
            "is_major_road": random.choice([True, False]),
            "citizen_urgent_flag": random.choice([True, False, False]),
            "simulated_visual_features": {
                "edge_density": round(random.uniform(0.04, 0.18), 4),
                "texture_variance": round(random.uniform(0.02, 0.12), 4),
                "valid": True
            }
        }
        dataset.append(sample)

    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"Generated {len(dataset)} annotated benchmark records -> {output_path}")
    return dataset

def generate_dataset(num_samples: int = 250, output_path: str = "research/data/benchmark_dataset.json"):
    return generate_benchmark_dataset(num_samples, output_path)

if __name__ == "__main__":
    generate_benchmark_dataset()
