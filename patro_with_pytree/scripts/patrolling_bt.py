import py_trees
import py_trees.behaviours as behaviours
import py_trees_ros.trees
import rclpy
from geometry_msgs.msg import PoseStamped
from py_trees_ros import subscribers, action_clients


class GoToPose(py_trees.behaviour.Behaviour):
    def __init__(self, name, pose):
        super(GoToPose, self).__init__(name)
        self.pose = pose
        self.publisher = None

    def setup(self, **kwargs):
        self.node = kwargs.get("node", None)
        if self.node:
            self.publisher = self.node.create_publisher(PoseStamped, "/goal_pose", 10)
        return True

    def update(self):
        if self.publisher is None:
            return py_trees.common.Status.FAILURE

        goal_msg = PoseStamped()
        goal_msg.header.frame_id = "map"
        goal_msg.pose.position.x = self.pose[0]
        goal_msg.pose.position.y = self.pose[1]
        goal_msg.pose.orientation.w = 1.0

        self.publisher.publish(goal_msg)
        return py_trees.common.Status.SUCCESS


def create_patrolling_tree():
    root = py_trees.composites.Sequence(name="Patrol Sequence")

    waypoint_1 = GoToPose("GoTo Pose 1", (2.0, 3.0))
    waypoint_2 = GoToPose("GoTo Pose 2", (5.0, 1.0))

    patrol_loop = py_trees.composites.Sequence(name="Patrol Loop", memory=True)
    patrol_loop.add_children([waypoint_1, waypoint_2])

    root.add_child(patrol_loop)
    return root


def main():
    rclpy.init()
    node = rclpy.create_node("patrolling_bt")

    tree = create_patrolling_tree()
    tree.setup(node=node)

    tree_tick_rate = py_trees_ros.trees.BehaviourTree(tree)
    tree_tick_rate.setup(timeout=15.0)

    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(tree_tick_rate.node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        tree.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
