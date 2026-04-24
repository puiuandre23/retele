import socket

HOST        = '127.0.0.1'
PORT        = 9999
BUFFER_SIZE = 1024

clienti_conectati = {}

# structura pentru mesaje:
# cheia = id-ul mesajului
# valoarea = dictionar cu textul si autorul mesajului
mesaje = {}
urmatorul_id = 1

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))

print("=" * 50)
print(f"  SERVER UDP pornit pe {HOST}:{PORT}")
print("  Asteptam mesaje de la clienti...")
print("=" * 50)

while True:
    try:
        date_brute, adresa_client = server_socket.recvfrom(BUFFER_SIZE)
        mesaj_primit = date_brute.decode('utf-8').strip()

        parti = mesaj_primit.split(' ', 1)
        comanda = parti[0].upper()
        argumente = parti[1] if len(parti) > 1 else ''

        print(f"\n[PRIMIT] De la {adresa_client}: '{mesaj_primit}'")

        if comanda == 'CONNECT':
            if adresa_client in clienti_conectati:
                raspuns = "EROARE: Esti deja conectat la server."
            else:
                clienti_conectati[adresa_client] = True
                nr_clienti = len(clienti_conectati)
                raspuns = f"OK: Conectat cu succes. Clienti activi: {nr_clienti}"
                print(f"[SERVER] Client nou conectat: {adresa_client}")

        elif comanda == 'DISCONNECT':
            if adresa_client in clienti_conectati:
                del clienti_conectati[adresa_client]
                raspuns = "OK: Deconectat cu succes. La revedere!"
                print(f"[SERVER] Client deconectat: {adresa_client}")
            else:
                raspuns = "EROARE: Nu esti conectat la server."

        elif comanda == 'PUBLISH':
            if adresa_client not in clienti_conectati:
                raspuns = "EROARE: Trebuie sa fii conectat pentru a publica mesaje."
            elif argumente.strip() == '':
                raspuns = "EROARE: Mesajul nu poate fi gol."
            else:
                id_mesaj = urmatorul_id
                mesaje[id_mesaj] = {
                    'text': argumente.strip(),
                    'autor': adresa_client
                }
                urmatorul_id += 1
                raspuns = f"OK: Mesaj publicat cu ID={id_mesaj}"

        elif comanda == 'DELETE':
            if adresa_client not in clienti_conectati:
                raspuns = "EROARE: Trebuie sa fii conectat pentru a sterge mesaje."
            elif argumente.strip() == '':
                raspuns = "EROARE: Trebuie sa specifici ID-ul mesajului."
            elif not argumente.strip().isdigit():
                raspuns = "EROARE: ID-ul trebuie sa fie un numar intreg valid."
            else:
                id_mesaj = int(argumente.strip())

                if id_mesaj not in mesaje:
                    raspuns = "EROARE: Nu exista mesaj cu acest ID."
                elif mesaje[id_mesaj]['autor'] != adresa_client:
                    raspuns = "EROARE: Nu poti sterge un mesaj publicat de alt client."
                else:
                    del mesaje[id_mesaj]
                    raspuns = f"OK: Mesajul cu ID={id_mesaj} a fost sters."

        elif comanda == 'LIST':
            if adresa_client not in clienti_conectati:
                raspuns = "EROARE: Trebuie sa fii conectat pentru a vedea mesajele."
            elif len(mesaje) == 0:
                raspuns = "OK: Nu exista mesaje publicate."
            else:
                linii = ["OK: Lista mesajelor:"]
                for id_mesaj, mesaj in mesaje.items():
                    linii.append(f"ID={id_mesaj}: {mesaj['text']}")
                raspuns = "\n".join(linii)

        else:
            raspuns = f"EROARE: Comanda '{comanda}' este necunoscuta. Comenzi valide: CONNECT, DISCONNECT, PUBLISH, DELETE, LIST"

        server_socket.sendto(raspuns.encode('utf-8'), adresa_client)
        print(f"[TRIMIS]  Catre {adresa_client}: '{raspuns}'")

    except KeyboardInterrupt:
        print("\n[SERVER] Oprire server...")
        break
    except Exception as e:
        print(f"[EROARE] {e}")

server_socket.close()
print("[SERVER] Socket inchis.")
