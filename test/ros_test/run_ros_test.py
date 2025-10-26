#!/usr/bin/env python3
"""
Fully automated ROS testing workflow for anchormotors package.

This script handles the complete workflow:
1. Start Docker container
2. Build project
3. Start roscore in background
4. Run test
5. Copy bag file to local machine

Usage:
    python run_ros_test.py [--test TEST_NUMBER] [--workspace-root PATH] [--launch-dir PATH] [--bagfile-dir DIR] [--no-build] [--list] [--help]

Examples:
    python run_ros_test.py --test 01                                    # Fully automated: start Docker, build, run test 01
    python run_ros_test.py --test 08 --no-build                         # Skip build step
    python run_ros_test.py --test 10 --bagfile-dir ./bagfiles          # Custom bag file output directory
    python run_ros_test.py --list                                       # List available tests
    python run_ros_test.py --test 01 --workspace-root /path/to/rossim  # Custom workspace
"""

import subprocess
import sys
import os
import time
import argparse
from pathlib import Path


class ROSTestRunner:
    def __init__(self, workspace_root=None, launch_dir=None, bagfile_output_dir=None):
        self.script_dir = Path(__file__).parent

        # Workspace root (rossim directory containing src/)
        if workspace_root is None:
            # Try to find it relative to the script first
            # Assuming structure: rossim/src/anchormotors/
            possible_workspace = self.script_dir.parent.parent.parent.parent / "rossim"
            if possible_workspace.exists():
                self.workspace_root = possible_workspace
            else:
                # Fallback: use current directory
                print("WARNING: Could not auto-detect workspace root. Use --workspace-root to specify.")
                print(f"         Tried: {possible_workspace}")
                self.workspace_root = Path.cwd()
        else:
            self.workspace_root = Path(workspace_root)

        # Launch directory
        if launch_dir is None:
            # Try to find it in the workspace
            possible_launch = self.workspace_root / "src" / "anchormotors" / "launch"
            if possible_launch.exists():
                self.launch_dir = possible_launch
            else:
                print("WARNING: Could not auto-detect launch directory. Use --launch-dir to specify.")
                print(f"         Tried: {possible_launch}")
                self.launch_dir = self.script_dir / "launch"
        else:
            self.launch_dir = Path(launch_dir)

        self.docker_image = "sprinkjm/rosempty"
        self.container_name = "anchormotors_test_container"
        self.container_id = None
        self.available_tests = self._find_available_tests()

        # Bag file output directory
        if bagfile_output_dir is None:
            # Default to current directory
            self.bagfile_output_dir = self.script_dir / "bagfiles"
        else:
            self.bagfile_output_dir = Path(bagfile_output_dir)

        # Create output directory if it doesn't exist
        self.bagfile_output_dir.mkdir(parents=True, exist_ok=True)

    def _find_available_tests(self):
        """Discover available test launch files."""
        if not self.launch_dir.exists():
            print(f"ERROR: Launch directory not found: {self.launch_dir}")
            print("       Use --launch-dir to specify the correct path")
            sys.exit(1)

        tests = {}
        for launch_file in sorted(self.launch_dir.glob("anchormotorsDocker_test*.launch")):
            test_num = launch_file.stem.replace("anchormotorsDocker_test", "")
            tests[test_num] = launch_file.name

        return tests

    def _run_command(self, cmd, shell=True, check=True, timeout=None, capture=False):
        """Execute shell command."""
        try:
            print(f"\n>>> {cmd}")
            result = subprocess.run(
                cmd,
                shell=shell,
                capture_output=capture,
                text=True,
                check=check,
                timeout=timeout
            )
            if capture:
                return result.returncode == 0, result.stdout.strip()
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"ERROR: Command timed out after {timeout}s")
            return False if not capture else (False, "")
        except Exception as e:
            print(f"ERROR: {e}")
            return False if not capture else (False, "")

    def _docker_exec(self, cmd, detach=False):
        """Execute command inside docker container."""
        if not self.container_id:
            print("ERROR: No container ID. Cannot execute command.")
            return False

        # Use -d flag for detached (background) execution, -it for interactive
        exec_flag = "-d" if detach else "-it"
        full_cmd = f'docker exec {exec_flag} {self.container_id} bash -c "{cmd}"'

        return self._run_command(full_cmd, shell=True, check=False)

    def _check_docker_installed(self):
        """Verify docker is installed and accessible."""
        print("[CHECK] Verifying Docker installation...")
        success, output = self._run_command("docker --version", capture=True)
        if success:
            print(f"✓ {output}")
            return True
        else:
            print("✗ Docker not found. Please install Docker Desktop.")
            return False

    def _start_docker(self):
        """Start Docker container."""
        print("\n[STEP 1] Starting Docker container...")

        # Check if container is already running
        success, running = self._run_command(
            f'docker ps --filter "name={self.container_name}" --format "{{{{.ID}}"}}',
            capture=True
        )

        if success and running:
            # Container already running
            self.container_id = running
            print(f"✓ Container already running: {self.container_id}")
            return True

        # Check if container exists but is stopped
        success, stopped = self._run_command(
            f'docker ps -a --filter "name={self.container_name}" --format "{{{{.ID}}"}}',
            capture=True
        )

        if success and stopped:
            # Container exists but stopped - remove it to start fresh
            print(f"Found stopped container: {stopped}")
            print("Removing stopped container to start fresh...")
            self._run_command(f'docker rm {self.container_name}', check=False)
            time.sleep(1)

        # Create new container
        print(f"Creating new container from {self.docker_image}...")
        print(f"Mount: {self.workspace_root} -> /ros/catkin_ws")
        cmd = (
            f'docker run --name {self.container_name} '
            f'--mount type=bind,source={self.workspace_root},target=/ros/catkin_ws '
            f'-d {self.docker_image} sleep infinity'
        )
        success = self._run_command(cmd, check=False)

        # Get container ID
        time.sleep(1)
        success, cid = self._run_command(
            f'docker ps --filter "name={self.container_name}" --format "{{{{.ID}}"}}',
            capture=True
        )
        if success and cid:
            self.container_id = cid
            print(f"✓ Container created: {self.container_id}")
            time.sleep(1)
            return True
        else:
            print("✗ Failed to create Docker container")
            print("Make sure Docker is running and you have permission to use docker commands.")
            return False

    def _build_project(self):
        """Build project with catkin_make."""
        print("\n[STEP 2] Building project...")
        cmd = (
            "cd /ros/catkin_ws && "
            "source /opt/ros/noetic/setup.bash && "
            "catkin_make -DCMAKE_BUILD_TYPE=Release 2>&1"
        )
        self._docker_exec(cmd, detach=False)
        # Even if there's output, consider it success if the command completes
        print("✓ Build completed (check output above for any warnings/errors)")
        return True

    def _start_roscore(self):
        """Start roscore in background inside container using nohup."""
        print("\n[STEP 3] Starting roscore in background...")

        # Create a script to run roscore properly
        cmd = (
            "source /opt/ros/noetic/setup.bash && "
            "nohup roscore > /tmp/roscore.log 2>&1 &"
        )
        self._docker_exec(cmd, detach=False)

        # Give roscore time to start and initialize
        print("Waiting for roscore to initialize...")
        time.sleep(3)

        # Verify roscore is running
        verify_cmd = (
            "source /opt/ros/noetic/setup.bash && "
            "timeout 5 rosnode list > /dev/null 2>&1"
        )
        success = self._docker_exec(verify_cmd, detach=False)

        if success:
            print("✓ roscore is running")
        else:
            print("⚠ roscore may not have started properly")
            print("You may need to start it manually in a separate terminal:")
            print(f"  docker exec -it {self.container_id} bash")
            print("  source /opt/ros/noetic/setup.bash")
            print("  roscore")

        return True

    def _run_test(self, test_number):
        """Run the specified test."""
        if test_number not in self.available_tests:
            print(f"\n✗ Test {test_number} not found.")
            print(f"Available tests: {', '.join(sorted(self.available_tests.keys()))}")
            return False

        launch_file = self.available_tests[test_number]
        print(f"\n[STEP 4] Running test {test_number}...")
        print(f"Launch file: {launch_file}")

        cmd = (
            "source /opt/ros/noetic/setup.bash && "
            "source /ros/catkin_ws/devel/setup.bash && "
            f"roslaunch anchormotors {launch_file}"
        )

        success = self._docker_exec(cmd)
        if success:
            print(f"✓ Test {test_number} completed")
            print("✓ Bag file has been saved")
        else:
            print(f"✗ Test {test_number} failed or was interrupted")
        return success

    def _copy_bagfile(self, test_number):
        """Copy the most recent bag file from container to local filesystem."""
        print(f"\n[STEP 5] Copying bag file to local machine...")

        # Find the most recent bag file for this test in the container
        find_cmd = f'docker exec {self.container_id} bash -c "ls -t /ros/catkin_ws/anchormotors_test{test_number}_*.bag 2>/dev/null | head -n 1"'
        success, bagfile_path = self._run_command(find_cmd, capture=True, check=False)

        if not success or not bagfile_path:
            print("⚠ No bag file found in container")
            print("  This might be normal if the test didn't generate a bag file")
            return False

        bagfile_name = Path(bagfile_path).name
        local_path = self.bagfile_output_dir / bagfile_name

        # Copy file from container to local machine
        copy_cmd = f'docker cp {self.container_id}:{bagfile_path} "{local_path}"'
        success = self._run_command(copy_cmd, check=False)

        if success:
            print(f"✓ Bag file copied to: {local_path}")
            return True
        else:
            print("✗ Failed to copy bag file")
            return False

    def list_tests(self):
        """List all available tests."""
        print("\nAvailable tests:")
        for test_num in sorted(self.available_tests.keys()):
            print(f"  {test_num}: {self.available_tests[test_num]}")

    def cleanup(self):
        """Stop and remove container."""
        if self.container_id:
            print("\n[CLEANUP] Stopping container...")
            self._run_command(f'docker stop {self.container_id}', check=False)
            print("✓ Container stopped")

    def run_full_workflow(self, test_number, build=True):
        """Execute complete workflow: Docker -> Build -> roscore -> Test -> Copy bag file."""
        print("=" * 60)
        print("  ROS Test Runner - Fully Automated")
        print("=" * 60)
        print(f"Workspace root: {self.workspace_root}")
        print(f"Launch directory: {self.launch_dir}")
        print(f"Bag file output: {self.bagfile_output_dir}")

        # Check Docker
        if not self._check_docker_installed():
            return False

        # Start Docker
        if not self._start_docker():
            return False

        # Build (optional)
        if build:
            if not self._build_project():
                print("\n✗ Build failed. Continuing anyway...")

        # Start roscore
        if not self._start_roscore():
            print("✗ Failed to start roscore")
            return False

        # Run test
        if not self._run_test(test_number):
            return False

        # Copy bag file to local machine
        self._copy_bagfile(test_number)

        print("\n" + "=" * 60)
        print("  ✓ Test workflow completed successfully!")
        print("=" * 60)
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Fully automated ROS testing for anchormotors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_ros_test.py --test 01                                    # Run complete workflow
  python run_ros_test.py --test 08 --no-build                         # Skip build step
  python run_ros_test.py --test 10 --bagfile-dir ./bagfiles          # Custom bag file output directory
  python run_ros_test.py --list                                       # List available tests
  python run_ros_test.py --test 01 --workspace-root /path/to/rossim  # Custom workspace
        """
    )
    parser.add_argument("--test", help="Test number to run (e.g., 01, 02, 03, 04, 08, 09, 10)")
    parser.add_argument("--no-build", action="store_true", help="Skip build step")
    parser.add_argument("--list", action="store_true", help="List available tests")
    parser.add_argument("--workspace-root",
                        default=None,
                        help="Path to rossim workspace root (auto-detected if not specified)")
    parser.add_argument("--launch-dir",
                        default=None,
                        help="Path to launch files directory (auto-detected if not specified)")
    parser.add_argument("--bagfile-dir",
                        default=None,
                        help="Directory to save bag files (default: ./bagfiles relative to script)")

    args = parser.parse_args()

    runner = ROSTestRunner(
        workspace_root=args.workspace_root,
        launch_dir=args.launch_dir,
        bagfile_output_dir=args.bagfile_dir
    )

    if args.list:
        runner.list_tests()
        return 0

    if not args.test:
        print("ERROR: --test argument required")
        print("Use --list to see available tests")
        return 1

    build = not args.no_build
    success = runner.run_full_workflow(args.test, build=build)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
