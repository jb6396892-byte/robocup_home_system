#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  printf '请用 source 执行：source scripts/setup_env.bash\n' >&2
  exit 2
fi

_robocup_source_required() {
  if [[ -f "$1" ]]; then
    # shellcheck disable=SC1090
    source "$1"
  else
    printf '环境加载失败：找不到 %s（%s）\n' "$1" "$2" >&2
    return 1
  fi
}

_robocup_repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export ROBOCUP_HOME_WS="${ROBOCUP_HOME_WS:-$(cd -- "${_robocup_repo_dir}/../.." && pwd)}"
export ROBOCUP_WPR_WS="${ROBOCUP_WPR_WS:-${HOME}/wpr_ros2_ws}"
export ROBOCUP_FRANKA_WS="${ROBOCUP_FRANKA_WS:-${HOME}/franka_ros2_ws}"

_robocup_source_required /opt/ros/humble/setup.bash 'ROS 2 Humble' || return 1
_robocup_source_required "${ROBOCUP_WPR_WS}/install/setup.bash" 'WPR 工作空间' || return 1
_robocup_source_required "${ROBOCUP_FRANKA_WS}/install/setup.bash" 'Franka 工作空间' || return 1

if [[ -f "${ROBOCUP_HOME_WS}/install/setup.bash" ]]; then
  _robocup_source_required "${ROBOCUP_HOME_WS}/install/setup.bash" '比赛总工作空间' || return 1
fi

unset _robocup_repo_dir
unset -f _robocup_source_required
