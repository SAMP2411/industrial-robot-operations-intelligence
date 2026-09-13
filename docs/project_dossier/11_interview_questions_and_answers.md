# Interview Questions And Answers

## Phase 1

### Why did you choose to resend the waypoint list after each round?

I wanted the mission layer to own round boundaries explicitly. One Nav2 goal equals one round, so it becomes easy to detect completion, print summaries, pause, stop, or trigger later inspection and operator logic. Repeating the full route upfront would make those boundaries blurrier.

### Why did you put the mission node in C++?

Because the project is meant to be hireable for robotics roles, and I wanted stronger systems signal. ROS 2 and Nav2 are heavily C++ oriented, so using C++ for the mission layer made the design feel more native and easier to discuss in interviews.

## Phase 2

### Why use a Nav2 waypoint task executor plugin for inspection?

Because checkpoint-local work should happen exactly when Nav2 considers a waypoint reached. The plugin is the clean boundary between “drive to this checkpoint” and “do the inspection work after arrival”.

### Why did you start with controlled anomalies instead of a real gauge classifier?

Because the first risk was system integration, not perception accuracy. Controlled labels let me prove the end-to-end mission, logging, and reporting pipeline before introducing CV uncertainty.

## Phase 3

### Why did you create custom messages?

Because logs are not a stable system interface. I wanted inspection and round results to be machine-readable so reporting, dashboards, and future monitors could subscribe to clean contracts.

### Why separate the reporter node from the mission node?

Because writing files is a reporting responsibility, not a control responsibility. The mission node should stay focused on patrol policy. The reporter node can evolve independently without tangling the control path.

### Why use RViz markers if you already have CSV and reports?

Because they solve a different problem. CSV and reports are for after-action review. Markers are for live operator awareness and faster debugging while the robot is running.

## Phase 4

### Why add severity levels instead of a boolean anomaly flag?

Because operational decisions depend on how serious a result is. A warning and a critical alarm are both anomalies, but they should not trigger the same mission response.

### Why delay the round summary slightly?

Because the last inspection result can arrive just after Nav2 finishes the waypoint action. The short synchronization delay ensures the round summary and policy decision use complete inspection data.

### Why does the mission node own `HOLD`?

Because `HOLD` is a mission-level decision based on multiple inputs: navigation outcome, inspection severity, and capture health. The waypoint plugin should publish facts, not decide global mission policy.

### What was the hardest engineering issue you solved?

The Gazebo Fuel dependency in the benchmark world. Visual launches sometimes failed before simulation started, which made verification unreliable. I fixed it by vendoring the benchmark models locally and launching a fully offline world, which made the visual benchmark reproducible.

## System-Level Questions

### How is the system layered?

Nav2 owns motion and waypoint execution. The mission node owns patrol rounds and policy. The waypoint plugin owns inspection-at-arrival. The report node owns persistence and presentation artifacts.

### What would you replace first for a production upgrade?

The controlled inspection labels. I would keep the same interfaces and replace the classifier stub with a real image analysis component so the system architecture remains stable while the perception layer becomes smarter.

### What makes this project stronger than a simple Nav2 demo?

It does more than move. It turns navigation into a mission workflow with evidence capture, live visualization, structured reporting, safety decisions, and reproducible verification.

## Quick-Fire Questions

### Why actions over services?

Because patrol is long-running and needs feedback plus a final result.

### Why YAML for checkpoints?

Because route and inspection expectations should be editable without recompiling.

### Why transient-local markers?

Because late RViz subscribers should still see already-published anomaly markers.

### Why benchmark first?

Because debugging mission logic and world-building at the same time makes failures harder to isolate.

