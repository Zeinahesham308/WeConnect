import concurrent.futures
import subprocess
import time
import matplotlib.pyplot as plt
import socket


def get_local_ip():
    return socket.gethostbyname(socket.gethostname())


def run_single_peer(peer_id, ip_addresses):
    start_time = time.time()
    subprocess.Popen(["start", "cmd", "/c", "python", "peer.py", str(peer_id), *ip_addresses], shell=True)
    peer_time = time.time() - start_time
    print(f"Peer {peer_id} took {peer_time:.2f} seconds to connect")
    return peer_time


def simulate_parallel_users(num_users):
    ip_addresses = [get_local_ip() for _ in range(num_users)]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        execution_times = list(executor.map(run_single_peer, range(1, num_users + 1), [ip_addresses] * num_users))

    return execution_times


def plot_execution_times(execution_times, num_users):
    peer_indices = list(range(1, num_users + 1))

    plt.plot(peer_indices, execution_times, marker='o', linestyle='-', color='b')
    plt.xlabel('Peer Index')
    plt.ylabel('Execution Time (seconds)')
    plt.title(f'Execution Time of peer.py for {num_users} Users')
    plt.show()


def main():
    for num_users_to_simulate in range(100, 1001, 100):
        print(f"Simulating {num_users_to_simulate} peers...")

        # Simulate parallel users
        start_time = time.time()
        execution_times = simulate_parallel_users(num_users_to_simulate)
        end_time = time.time()

        total_time = sum(execution_times)
        allconnection_time = end_time - start_time
        average_time = total_time / num_users_to_simulate

        print(f"All {num_users_to_simulate} peers connected in {allconnection_time:.2f} seconds")
        print(f"Average time taken per peer: {average_time:.2f} seconds")

        # Plot the execution times
        plot_execution_times(execution_times, num_users_to_simulate)

        # Prompt user to continue or abort
        user_input = input("Press Enter to continue or type 'q' to abort: ").strip().lower()
        if user_input == 'q':
            print("Aborting the simulation.")
            break


if __name__ == "__main__":
    main()
