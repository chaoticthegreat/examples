#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

from wpilib import XboxController
import commands2
import constants as Constants
from subsystems.drivesubsystems import DriveSubsystem
from wpimath.trajectory import Trajectory, TrajectoryConfig, TrajectoryGenerator
from wpimath.geometry import Translation2d, Pose2d, Rotation2d
from wpimath.controller import ProfiledPIDController, PIDController
import math


class RobotContainer:
    def __init__(self):
        """
        The robot's subsystems
        """
        self.robotDrive = DriveSubsystem()

        # Driver Controller
        self.driverController = XboxController(
            Constants.OIConstants.kDriverControllerPort
        )

        """
        Configure default commands
        """
        self.robotDrive.setDefaultCommand(
            # The left stick controls translation of the robot.
            # turning is controlled by the X axis of the right stick.
            commands2.RunCommand(
                lambda: self.robotDrive.drive(
                    # Multiply by max speed to map the joystick unitless inputs to actual units.
                    # This will map the [-1, 1] to [max speed backwards, max speed forwards],
                    # converting them to actual units.
                    self.driverController.getYChannel()
                    * Constants.DriveConstants.kMaxSpeedMetersPerSecond,
                    self.driverController.getXChannel()
                    * Constants.DriveConstants.kMaxSpeedMetersPerSecond,
                    self.driverController.getX(Constants.Hand.kRight)
                    * Constants.ModuleConstants.kMaxModuleAngularSpeedRadiansPerSecond,
                    False,
                ),
                self.robotDrive,
            )
        )

    def configureButtonBindings(self):
        pass

    def getAutonomousCommand(self):
        """
        Create config for trajectory
        """
        config = TrajectoryConfig(
            Constants.AutoConstants.kMaxSpeedMetersPerSecond,
            Constants.AutoConstants.kMaxAccelerationMetersPerSecondSquared,
        ).setKinematics(Constants.DriveConstants.kDriveKinematics)

        # An example trajectory to follow. All units in meters.

        example_trajectory = TrajectoryGenerator.generateTrajectory(
            # Start at the origin facing the +X direction
            Pose2d(0, 0, Rotation2d(0)),
            # Pass through these two interior waypoints, making an 's' curve path
            [Translation2d(1, 1), Translation2d(2, -1)],
            # End 3 meters straight ahead of where we started, facing forward
            Pose2d(3, 0, Rotation2d(0)),
            config,
        )

        theta_controller = ProfiledPIDController(
            Constants.AutoConstants.kPThetaController,
            0,
            0,
            Constants.AutoConstants.kThetaControllerConstraints,
        )
        theta_controller.enableContinuousInput(-math.pi, math.pi)

        swerve_controller_command = commands2.Swerve4ControllerCommand(
            example_trajectory,
            self.robotDrive.getPose,
            # Functional interface to feed supplier
            Constants.DriveConstants.kDriveKinematics,
            # Position controllers
            PIDController(Constants.AutoConstants.kPXController, 0, 0),
            PIDController(Constants.AutoConstants.kPYController, 0, 0),
            theta_controller,
            self.robotDrive.setModuleStates,
            self.robotDrive,
        )

        """
        Reset odometry to the initial pose of the trajectory, run path following
        command, then stop at the end.
        """
        return commands2.Commands.sequence(
            commands2.InstantCommand(
                lambda: self.robotDrive.resetOdometry(
                    example_trajectory.getInitialPose()
                )
            ),
            swerve_controller_command,
            commands2.InstantCommand(lambda: self.robotDrive.drive(0, 0, 0, False)),
        )
