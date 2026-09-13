# Current Known Limitations

This document captures the current repository limitations based on code inspection and the July 18, 2026 smoke test.

## Product and Data Model Limitations

- there is now a SQLite-backed operator store for synced sites, assets, missions, evidence metadata, and findings, but the live ROS runtime does not yet publish directly into it
- the benchmark now has YAML-based asset registry and site config files, but not a persistent multi-site source-of-truth service
- the benchmark now has YAML-based inspection profile definitions, but not a runtime-managed product workflow around them
- the operator API/UI workflow is local MVP quality rather than production-hardened
- the finding acknowledgement / assignment / reinspection / resolution lifecycle exists in the operator console, but it is not yet coupled back into robot execution

## Inspection Limitations

- perception remains benchmark-grade rather than field-validated
- current anomaly logic still depends on synthetic benchmark setup
- there is no formal model registry or rule registry yet
- evidence quality is partly implied, not exposed as a standalone product-grade contract

## Mission Limitations

- planning is still route-first rather than fully asset-centered
- mission state is persisted in the operator console, but live mission orchestration does not yet consume operator-created missions
- no restart recovery with persisted mission resume
- there is a basic operator pause / cancel flow in the operator console, but not a live ROS runtime pause / cancel / approval bridge

## Robot Abstraction Limitations

- the strongest path is still the single-robot Nav2 benchmark
- multi-platform support exists but is not fully hardened
- multi-robot fleet support exists but is not yet fully verified end to end

## Reliability Limitations

- no formal unit-test suite
- only a small Python operator-workflow API test exists so far, not a broad integration suite
- no launch-test suite
- smoke test exists, but it validates route progress rather than a complete mission lifecycle
- no endurance/soak test framework yet

## Security and Deployment Limitations

- JWT-based tenant login now exists for the operator console, but there is no production-grade role or permission model yet
- finding-event history exists, but there is no full cross-service audit log program yet
- no SBOM/security scan pipeline in the repo
- no documented edge deployment package yet
- no backup/restore or migration framework yet

## What Is Already Strong

These limitations should be read together with the current strengths:

- working ROS 2 launch architecture
- working Nav2 integration
- working checkpoint inspection pipeline
- working evidence generation
- working report generation
- working mission-level decision logic

So the project is not “unfinished” in a weak sense. It is a strong prototype that still needs startup-grade operational layers around it.
