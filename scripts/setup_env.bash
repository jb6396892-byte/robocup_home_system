#!/usr/bin/env bash

_robocup_source_if_present() {
  if [[ -f "$1" ]]; then
    # shellcheck disable=SC1090
    source "$1"
  else
    printf 'robocup setup: missing %s\n' "$1" >&2
    return 1
  fi
}

_robocup_source_if_present /opt/ros/humble/setup.bash
_robocup_source_if_present /home/smg/wpr_ros2_ws/install/setup.bash
_robocup_source_if_present /home/smg/franka_ros2_ws/install/setup.bash

if [[ -f /home/smg/robocup_home_ws/install/setup.bash ]]; then
  _robocup_source_if_present /home/smg/robocup_home_ws/install/setup.bash
fi

unset -f _robocup_source_if_present
