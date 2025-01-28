import threading
import socket
import json
import random
import time
import logging
import os

# Get the environment variables for the container's ID and other settings
HOST = os.getenv("HOST", "0.0.0.0")
BASE_PORT = int(os.getenv("BASE_PORT", 5000))
PORT_RANGE = int(os.getenv("PORT_RANGE", 10))  # Number of agents to run
AGENT_ID = int(os.getenv("AGENT_ID", 0))  # Get agent ID from environment variable

# Logging setup to write to a shared volume
log_file = "/logs/agent_logs.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)


class Agent:
    def __init__(self, id: int):
        self.id = id
        self.tasks = set()
        self.assigned_task = None
        self.port = BASE_PORT + id
        self.neighbor_ports = []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, self.port))
        self.server_socket.listen()
        self.server_socket.settimeout(1)
        self.running = True

    def get_info(self):
        """Capture initial tasks."""
        tasks = list("abcde")
        number_of_tasks = random.randint(1, len(tasks))
        self.tasks.update(random.sample(tasks, number_of_tasks))
        logging.critical(f"Agent {self.id} initial tasks gathered: {self.tasks}")

    def listen_for_messages(self):
        """Listen for incoming task information."""
        while self.running:
            try:
                conn, _ = self.server_socket.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        message = json.loads(data.decode())
                        logging.info(f"Agent {self.id} received: {message}")
                        self.tasks.update(message["tasks"])
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logging.error(f"Agent {self.id} error: {e}")
                break

    def send_task_info(self):
        """Send task information to neighbors."""
        message = json.dumps({"id": self.id, "tasks": list(self.tasks)})
        for port in self.neighbor_ports:
            try:
                with socket.create_connection((HOST, port), timeout=1) as sock:
                    sock.sendall(message.encode())
                    logging.info(f"Agent {self.id} sent tasks to Agent at port {port}")
            except (ConnectionRefusedError, socket.timeout):
                logging.warning(
                    f"Agent {self.id} failed to connect to Agent at port {port}"
                )

    def discover_neighbors(self):
        """Scan ports within a range to find active neighbors."""
        for port in range(BASE_PORT, BASE_PORT + PORT_RANGE):
            if port != self.port:
                try:
                    with socket.create_connection((HOST, port), timeout=0.5) as sock:
                        self.neighbor_ports.append(port)
                        logging.info(
                            f"Agent {self.id} detected neighbor at port {port}"
                        )
                except (ConnectionRefusedError, socket.timeout):
                    continue

    def assign_unique_task(self, assigned_tasks):
        """Choose a unique task."""
        available_tasks = self.tasks - assigned_tasks
        if available_tasks:
            self.assigned_task = available_tasks.pop()
            assigned_tasks.add(self.assigned_task)
            logging.critical(
                f"Agent {self.id} assigned unique task: {self.assigned_task}"
            )
        else:
            logging.warning(f"Agent {self.id} found no available unique task")

    def run(self):
        """Main agent behavior."""
        self.get_info()

        # Start listener thread for incoming messages
        listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        listener_thread.start()

        # Discover neighbors by scanning ports
        time.sleep(1)  # Allow time for agents to start their servers
        self.discover_neighbors()

        # Network discovery phase: wait for 10 seconds
        time.sleep(10)
        logging.critical(f"Agent {self.id} completed network discovery.")

        # Broadcast task information
        self.send_task_info()

        # Wait for task propagation
        time.sleep(2)

        # Task assignment phase
        with result_lock:
            self.assign_unique_task(assigned_tasks)

        # Output gathered information and assigned task
        logging.critical(
            f"Agent {self.id} info gathered: {self.tasks}, assigned task: {self.assigned_task}"
        )

        # Close the socket and stop listening
        self.stop_listening()

    def stop_listening(self):
        """Close the server socket and stop the listening loop."""
        self.running = False
        self.server_socket.close()
        logging.info(f"Agent {self.id}: Server socket closed.")


# Shared resources
assigned_tasks = set()
result_lock = threading.Lock()

if __name__ == "__main__":
    agent = Agent(id=AGENT_ID)  # Use the agent ID from environment
    agent.run()
