import socket
import threading

PORT = 3333

clients = {}  # {connexion: nom}
lock = threading.Lock()

nom = input("Choisissez votre nom : ")


def envoyer_a_tous(message, sauf=None):
    """Envoie un message à tous les clients."""

    message = message + "\n"

    with lock:
        for client in list(clients):
            if client != sauf:
                try:
                    client.sendall(message.encode())
                except:
                    client.close()
                    del clients[client]


def gerer_client(conn, addr):
    """Gère un client connecté."""

    buffer = ""

    try:
        # Réception du nom
        data = conn.recv(1024).decode()

        if not data:
            conn.close()
            return

        nom_client = data.strip()

        with lock:
            clients[conn] = nom_client

        print(f"{nom_client} vient de se connecter ({addr[0]})")

        envoyer_a_tous(
            f"*** {nom_client} vient de rejoindre le chat. ***",
            sauf=conn
        )

        conn.sendall(
            f"*** Bienvenue {nom_client} ! ***\n".encode()
        )

        # Réception des messages
        while True:

            data = conn.recv(4096).decode()

            if not data:
                break

            buffer += data

            # Traiter tous les messages terminés par \n
            while "\n" in buffer:

                message, buffer = buffer.split("\n", 1)
                message = message.strip()

                if not message:
                    continue

                # Commande /quit
                if message == "/quit":
                    return

                # Commande /users
                if message == "/users":

                    with lock:
                        liste = ", ".join(clients.values())

                    conn.sendall(
                        f"*** Utilisateurs connectés : {liste} ***\n".encode()
                    )

                    continue

                # Message normal
                texte = f"[{nom_client}] {message}"

                print(texte)

                envoyer_a_tous(texte)

    except Exception as e:
        print(f"Erreur avec {addr[0]} : {e}")

    finally:

        with lock:
            nom_client = clients.pop(conn, None)

        conn.close()

        if nom_client:
            print(f"{nom_client} s'est déconnecté.")

            envoyer_a_tous(
                f"*** {nom_client} s'est déconnecté. ***"
            )


def serveur():
    """Lance le serveur."""

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server.bind(("0.0.0.0", PORT))
    server.listen()

    print()
    print("================================")
    print(f" Serveur lancé sur le port {PORT}")
    print("================================")
    print()

    # Thread pour accepter les clients
    threading.Thread(
        target=accepter_clients,
        args=(server,),
        daemon=True
    ).start()

    # Le serveur peut aussi écrire
    while True:

        try:
            message = input("> ")

            if not message:
                continue

            if message == "/users":

                with lock:
                    liste = ", ".join(clients.values())

                print(f"Utilisateurs connectés : {liste}")

                envoyer_a_tous(
                    f"*** Serveur : utilisateurs connectés : {liste} ***"
                )

            elif message == "/quit":

                envoyer_a_tous(
                    "*** Le serveur ferme la connexion. ***"
                )

                server.close()
                break

            else:

                texte = f"[{nom}] {message}"

                print(texte)

                envoyer_a_tous(texte)

        except KeyboardInterrupt:
            break


def accepter_clients(server):
    """Accepte plusieurs clients."""

    while True:

        try:
            conn, addr = server.accept()

            print(f"Nouvelle connexion : {addr[0]}")

            threading.Thread(
                target=gerer_client,
                args=(conn, addr),
                daemon=True
            ).start()

        except:
            break


def recevoir(conn):
    """Reçoit les messages du serveur."""

    buffer = ""

    while True:

        try:
            data = conn.recv(4096).decode()

            if not data:
                print("\nConnexion fermée par le serveur.")
                break

            buffer += data

            while "\n" in buffer:

                message, buffer = buffer.split("\n", 1)

                if message:
                    print(f"\n{message}")

                print("> ", end="", flush=True)

        except:
            break


def client(ip):
    """Connexion en tant que client."""

    conn = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    print(f"Connexion à {ip}:{PORT}...")

    conn.connect((ip, PORT))

    print("Connecté au serveur !")

    # Envoyer le nom
    conn.sendall((nom + "\n").encode())

    # Thread pour recevoir
    threading.Thread(
        target=recevoir,
        args=(conn,),
        daemon=True
    ).start()

    # Envoi des messages
    while True:

        try:
            message = input("> ")

            if not message:
                continue

            conn.sendall((message + "\n").encode())

            if message == "/quit":
                conn.close()
                break

        except:
            break


# ==========================
# PROGRAMME PRINCIPAL
# ==========================

mode = input(
    "Mode serveur (s) ou client (c) ? "
).lower()

if mode == "s":
    serveur()

elif mode == "c":
    ip = input("IP du serveur : ")
    client(ip)

else:
    print("Mode invalide.")