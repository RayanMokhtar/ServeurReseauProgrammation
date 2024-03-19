import socket
import psycopg2
from datetime import datetime
import uuid
from decimal import Decimal
import time
import sys
import logging
TAILLE_MAX_BUFFER = 1023 # Taille maximale du buffer en octets
# Paramètres de connexion à la base de données
db_host = "postgresql-bdizly.alwaysdata.net"
db_port = 5432
db_name = "bdizly_2023"
db_user = "bdizly"
db_password = "Izly2023"

# ici je configure le logging pour enregistrer les logs dans un fichier niveau : info
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M',
    filename='server_logs.txt',
    filemode='a' 
)
def connect_db():
    return psycopg2.connect(host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_password)

def obtenir_num_caisse(id_caisse):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT num_caisse FROM caisse WHERE id_caisse = %s", (id_caisse,))
            result = cursor.fetchone()
            return result[0] if result else None
        
def get_client_info(id_client):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT nom, prenom, solde, code_tarif
                FROM client_izly
                WHERE id_client = %s
            """, (id_client,))
            return cursor.fetchone()

def tracage_logs(client_id, id_caisse):
    with open("server_logs.txt", "a") as file:
        timestamp = time.strftime("%Y-%m-%d %H:%M")
        log_entry = f"la date : {timestamp} - Client ID: {client_id}, Numéro de Caisse: {id_caisse}\n"
        file.write(log_entry)

def inserer_commande(id_menu, id_produit, prix_commande):
    id_commande = str(uuid.uuid4())[:11]
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO commande (id_commande, id_menu, ref_produit, prix_commande)
                VALUES (%s, %s, %s, %s)
            """, (id_commande, id_menu, id_produit, prix_commande))
        conn.commit()
    return id_commande

def est_id_caisse_valide(id_caisse):
    return len(id_caisse) <= 11 and id_caisse.isalnum()


def obtenir_nom_caissier(id_caisse):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            query = """
                SELECT ca.nom_caissier
                FROM caisse ca
                WHERE ca.id_caisse = %s
            """
            cursor.execute(query, (id_caisse,))
            result = cursor.fetchone()
            return result[0] if result else "Caissier non trouvé"

def obtenir_adresse_resto(id_caisse):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            query = """
                SELECT ru.adresse_resto
                FROM caisse ca
                JOIN restaurant_universitaire ru ON ca.id_resto = ru.id_resto
                WHERE ca.id_caisse = %s
            """
            cursor.execute(query, (id_caisse,))
            result = cursor.fetchone()
            return result[0] if result else None

def valider_donnees_client(id_client):
    # Vérifier si l'ID du client ne dépasse pas 11 caractères yy
    if len(id_client) > 11:
        return False
    return True
def get_menu_izly():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_menu,type_menu, prix_menu FROM menu_izly")
            return cursor.fetchall()

def get_supplements():
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT  ref_produit,nom_produit,prix_produit FROM supplement")
            return cursor.fetchall()
        
def get_prix_supplements(ref_produit):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT prix_produit FROM supplement WHERE ref_produit = %s", (ref_produit,))
            result = cursor.fetchone()
            return result[0] if result else 0



def update_client_balance(id_client, montant_total):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE client_izly
                SET solde = solde - %s
                WHERE id_client = %s
                RETURNING solde
            """, (montant_total, id_client))
            return cursor.fetchone()[0]

def get_prix_menu(id_menu_selectionne):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT prix_menu FROM menu_izly
                WHERE id_menu = %s
            """, (id_menu_selectionne,))
            result = cursor.fetchone()
            return result[0] if result else None
        
def valider_donnees_client(id_client):
    # Vérifier si l'ID du client ne dépasse pas 11 caractères et ne contient pas de caractères spéciaux
    if len(id_client) > 11 or not id_client.isalnum():
        return False
    return True

def verifier_et_debiter_solde(id_client, solde, total_prix):
    if solde >= total_prix:
        # Mise à jour du solde du client après débit
        nouveau_solde = solde - total_prix
        with connect_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE client_izly
                    SET solde = %s
                    WHERE id_client = %s
                """, (nouveau_solde, id_client))
            conn.commit()
        return True, f"\nPaiement réussi. Nouveau solde: {nouveau_solde:.2f}£\n"
    else:
        return False, "Solde insuffisant. Paiement refusé."


def verifier_existence_caisse(id_caisse):
    try:
        with connect_db() as conn:  
            with conn.cursor() as cursor:
                # Vérification du format du numéro de caisse avant d'exécuter la requête
                if not id_caisse.isdigit():
                    print("l'id de la caisse saisie n'existe pas")
                    return False

                cursor.execute("SELECT * FROM caisse WHERE id_caisse = %s", (id_caisse,))
                return cursor.fetchone() is not None
    except psycopg2.errors.InvalidTextRepresentation as e:
        # Gestion de l'erreur de format SQL
        print(f"Erreur de format SQL pour le numéro de caisse : {e}")
        return False
    except psycopg2.DatabaseError as e:
        # Gestion des autres erreurs de la base de données
        print(f"Erreur de base de données : {e}")
        return False
    
def verifier_validite_supplement(supplement_choisi):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM supplement WHERE ref_produit = %s", (supplement_choisi,))
            return cursor.fetchone() is not None

def inserer_encaissement(id_client, date_commande, id_caisse, id_commande):
    with connect_db() as conn:
        with conn.cursor() as cursor:
            query = """
                INSERT INTO encaisser (id_client, date_commande, id_caisse, id_commande)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (id_client, date_commande, id_caisse, id_commande))
        conn.commit()

def demarrer_serveur(port):
    if not (0 <= port <= 65535):
        print(f"Le numéro de port spécifié {port} est hors de la plage valide (0-65535).")#gérer cas ou numéro de port entré est supérieur à 65535
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket: #échange tcp
       try: 
        server_socket.bind(('0.0.0.0', port))
       except OSError as e:
            if e.errno == 10048:  # Erreur de port déjà utilisé
                logging.error("Le port est déjà utilisé. Veuillez en choisir un autre.")
                print("Le port est déjà utilisé. Veuillez en choisir un autre.")
                return False
            else:
                raise
       server_socket.listen()
        

       while True:
            logging.info(f"Serveur en écoute sur le port {port}")
            print(f"Serveur en écoute sur le port {port}")
            client_socket, client_address = server_socket.accept()
            with client_socket:
                client_socket.settimeout(20)  # Définir un timeout de 10 secondes
                logging.info(f"Connexion établie avec {client_address}")
                print(f"Connexion établie avec {client_address}")
                #time.sleep(25) cette commande indique que le serveur sera endormi pendant 25 secondes , nécessaire afin de voir l'exception coté client : inactivité du serveur
                try:
                    id_caisse = client_socket.recv(TAILLE_MAX_BUFFER + 1).decode('utf-8').strip()
                    if len(id_caisse) > TAILLE_MAX_BUFFER:
                        logging.error("Données reçues dépassant la taille maximale du buffer. Fermeture de la connexion.")
                        print("Données reçues dépassant la taille maximale du buffer. Fermeture de la connexion.")
                        client_socket.close()
                        continue
                    else:
                        print("Numéro de caisse reçu : ", id_caisse)
                    
                    client_info = None
                    resultat=verifier_existence_caisse(id_caisse)  
                    if not est_id_caisse_valide(id_caisse):
                        client_socket.sendall("ID de la caisse invalide. Veuillez réessayer.\n".encode('utf-8'))
                        client_socket.close()
                        continue  
                    
                    if not resultat:
                        message_erreur = "Erreur de format du numéro de caisse ou de numéro de caisse. Déconnexion...\n"
                        client_socket.sendall(message_erreur.encode('utf-8'))
                        logging.error("erreur de format détectée , client déconnecté")
                        print("Erreur dans la saisie de l'id de la caisse , déconnecté.")

                        client_socket.close()
                        continue  
                        
                    elif resultat is not None:
                        client_socket.sendall("Numéro de caisse valide ,Ce Terminal_Izly appartient au CROUS, Continuons...\n".encode('utf-8'))
                        num_caisse=obtenir_num_caisse(id_caisse)
                        print(f"Transaction sur la caisse avec le numéro {num_caisse}")
                        print("En attente de la saisie de l'id du Client")
                        id_client = client_socket.recv(1024).decode('utf-8').strip()
                        tracage_logs(id_client, id_caisse) #fonction pour le tracage 
                        if not valider_donnees_client(id_client):
                    # Si les données du client ne sont pas valides, envoyer un message d'erreur et fermer la connexion (  vérification coté serveur avant d'envoyer la requete sql )
                            client_socket.sendall("ID client non valide (trop long ou contient des caractères spéciaux). Veuillez réessayer.\n".encode('utf-8'))
                            client_socket.close()
                            continue
                        client_info = get_client_info(id_client)
                    else:
                        message_erreur = "Numéro de caisse non valide ou erreur de format\n"
                        client_socket.sendall(message_erreur.encode('utf-8'))
                        print("Numéro de caisse non valide ou erreur de format, client déconnecté.")
                        client_socket.close()
                        continue
                        
                    
                    
                    if client_info:
                        nom,prenom, solde, code_tarif = client_info
                        response = f"ID client valide , Bienvenue : {nom},{prenom}\nvotre solde actuel est de: {solde} £ \nCode tarif: {code_tarif}\n"
                        reduction = 0
                        if code_tarif == "98":
                            response += "vous etes boursier , la réduction a été prise en compte.\n"
                            reduction = 2.30

                        # Envoi de la liste des menus
                        menu_data = get_menu_izly()
                        print("Saisie du menu en cours : ")
                        menu_response = "Menu Izly:\n" + "".join([f"{id_menu}:{type_menu}: {prix_menu} £\n" for id_menu, type_menu, prix_menu in menu_data]) + "---- Fin de la liste des menus ----\n"

                        prix_menu_selectionne = None
                        for _ in range(3):  # Trois tentatives pour le menu
                            client_socket.sendall((response + menu_response).encode('utf-8'))
                            type_menu_selectionne = client_socket.recv(1024).decode('utf-8').strip()
                            prix_menu_selectionne = get_prix_menu(type_menu_selectionne)

                            if prix_menu_selectionne is not None:
                                total_prix = prix_menu_selectionne
                                break
                            else:
                                client_socket.sendall("Menu sélectionné non valide. Veuillez réessayer.\n".encode('utf-8'))

                        # Gestion des suppléments si un menu valide est sélectionné
                        if prix_menu_selectionne is not None:
                            supplement_choisi = None
                            while True:
                                client_socket.sendall("Avez-vous pris un supplement ? (oui/non)\n".encode('utf-8'))
                                reponse_supplement = client_socket.recv(1024).decode('utf-8').strip()

                                if reponse_supplement.lower() == 'oui':
                                    supplements = get_supplements()
                                    print("saisie du supplément en cours :")
                                    supplement_response = "Veuillez sélectionner un supplément par son ID : exemple pour Coca-Cola rentrer PROD000001\nListe des suppléments :\n" + "".join([f"{ref_produit}:{nom_produit}: {prix_produit} £\n" for ref_produit, nom_produit, prix_produit in supplements]) + "---- Fin de la liste des suppléments ----\n"
                                    client_socket.sendall(supplement_response.encode('utf-8'))
                                    supplement_choisi = client_socket.recv(1024).decode('utf-8').strip()
                                    if not verifier_validite_supplement(supplement_choisi):
                                        client_socket.sendall("Supplément non valide, paiement refusé.\n".encode('utf-8'))
                                        client_socket.close()
                                        break
                                    else:
                                        prix_supp = get_prix_supplements(supplement_choisi)
                                        total_prix += prix_supp
                                        reduction_decimal = Decimal(str(reduction))
                                        total_prix = total_prix - reduction_decimal
                                        break
                                elif reponse_supplement.lower() == 'non':
                                    print("Aucun supplément n'a été choisi.")
                                    reduction_decimal = Decimal(str(reduction))
                                    total_prix = total_prix - reduction_decimal
                                    break
                                else:
                                    client_socket.sendall("Réponse non reconnue. Veuillez répondre par 'oui' ou 'non'.\n".encode('utf-8'))

                            # Vérifier le solde et débiter si la situation le permet
                            success, message = verifier_et_debiter_solde(id_client, solde, total_prix)
                            client_socket.sendall(message.encode('utf-8'))

                            if success:
                                # Insérer dans la table commande et dans la table encaisser afin de pouvoir accéder dans l'historique 
                                date_commande = datetime.now().strftime("%Y-%m-%d %H:%M")
                                id_commande = inserer_commande(type_menu_selectionne, supplement_choisi, total_prix)
                                inserer_encaissement(id_client, date_commande, id_caisse, id_commande)

                                

                                # Obtenir l'adresse du restaurant et le nom du caissier avec les fonctions prédéfinies dans le code 
                                adresse_resto = obtenir_adresse_resto(id_caisse)
                                nom_caissier = obtenir_nom_caissier(id_caisse)

                                # Construire et envoyer le ticket de la commande ( impression du ticket dans le diagramme)
                                ticket = (
                                    f"\nTicket de Commande :\n"
                                    f"Nom : {client_info[0]}\n"
                                    f"Prénom : {client_info[1]}\n"
                                    f"ID Commande : {id_commande}\n"
                                    f"Date : {date_commande}\n"
                                    f"Lieu : {adresse_resto}\n"
                                    f"Nom Caissier : {nom_caissier}\n"
                                    f"Prix Total : {total_prix:.2f} £\n"
                                )

                                client_socket.sendall(ticket.encode('utf-8'))
                            else:
                                logging.error("erreur dans la saisie de la commande")
                                print("erreur dans la saisie de la commande.")
                    else:
                        response = "ID client non valide\n"
                        client_socket.sendall(response.encode('utf-8'))

                    
                except KeyboardInterrupt:
                    logging.error("\nArrêt du serveur suite à une interruption clavier (Ctrl+C).")
                    print("\nArrêt du serveur suite à une interruption clavier (Ctrl+C).")
                except socket.timeout:
                    logging.error("Le client a mis trop de temps pour répondre. Déconnexion.")
                    print("Le client a mis trop de temps pour répondre. Déconnexion.")
                    client_socket.close()
                except ConnectionAbortedError :
                    logging.error("Connexion abandonnée par le client.")
                    print("Connexion abandonnée par le client.")    
                except ConnectionResetError:
                    logging.error("Connexion perdue brusquement avec le client.")
                    print("Connexion perdue brusquement avec le client.")
                
                except socket.gaierror:
                    logging.error("Erreur de résolution DNS.") 
                    print("Erreur de résolution DNS.")   
                except socket.error as e:
                    if e.errno == 10038:
                        logging.error("Une opération a été tentée sur autre chose qu’un socket , ce qui ferme le client .")
                        print("Une opération a été tentée sur autre chose qu’un socket , ce qui ferme le client .")
                    else:
                        if e.errno == 98:  # Erreur de port déjà utilisé
                            logging.error("Le port est déjà utilisé. Veuillez en choisir un autre.")
                            print("Le port est déjà utilisé. Veuillez en choisir un autre.") 
                        elif e.errno==10054:
                            logging.error("le client s'est déconnecté brusquement !")
                            print("le client s'est déconnecté brusquement !")
                        else:
                            logging.error(f"Erreur de socket et voici le type d'erreur : {e}")
                            print(f"Erreur de socket et voici le type d'erreur : {e}")
                except Exception as e:
                    logging.error(f"Une erreur inattendue est survenue: {e}")
                    print(f"Une erreur inattendue est survenue: {e}")
                    
                
                finally:
                    print("Fin de la connexion avec le client.")
                    logging.error("Fin de la connexion avec le client.")
                    client_socket.close()

PORT_PAR_DEFAUT = 12344 #le numéro de port par défaut

if __name__ == "__main__":
    port_specifie = PORT_PAR_DEFAUT #définir le port par défaut 

    if len(sys.argv) > 1:
        try:
            port_specifie = int(sys.argv[1]) #récupérer le port en argument
        except ValueError:
            print("Le port doit être un nombre. Utilisation du port par défaut.")
            logging.error("Le port doit être un nombre. Utilisation du port par défaut.")

    if not demarrer_serveur(port_specifie):
        logging.info(f"Tentative de démarrage sur le port par défaut : {PORT_PAR_DEFAUT}")
        print(f"Tentative de démarrage sur le port par défaut : {PORT_PAR_DEFAUT}")
        demarrer_serveur(PORT_PAR_DEFAUT)