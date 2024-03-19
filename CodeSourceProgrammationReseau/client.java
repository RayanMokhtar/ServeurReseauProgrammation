import java.io.*;
import java.net.Socket;
import java.net.SocketException;
import java.net.SocketTimeoutException;
import java.net.ConnectException;
import java.net.BindException;
import java.net.UnknownHostException;
import java.net.NoRouteToHostException;
import java.util.Scanner;
import java.util.logging.Logger;
import java.util.logging.Level;
import java.util.logging.FileHandler;
import java.util.logging.SimpleFormatter;
import java.util.logging.Formatter;
import java.util.logging.LogRecord;



public class Client {
   
    private static final int TIMEOUT = 20000; // 20 secondes
    private static final Logger logger = Logger.getLogger(Client.class.getName());

    private static class MyCustomFormatter extends Formatter { /*customiser l'affichage des logger */
        @Override
        public String format(LogRecord record) {
            // Retourner uniquement le message du log
            return record.getMessage() + "\n";
        }
    }

    static {
        try {
            FileHandler fh = new FileHandler("client_logs.txt", true);
            fh.setFormatter(new MyCustomFormatter());
            logger.addHandler(fh);
            logger.setUseParentHandlers(false);
        } catch (IOException e) {
            logger.log(Level.SEVERE, "Erreur lors de la configuration du logger", e);
        }
    }
    private static boolean estIdClientValide(String idClient) {
        return idClient.length() <= 11 && idClient.matches("[a-zA-Z0-9]+");
    }
    private static boolean estIdCaisseValide(String idCaisse) {
    return idCaisse.length() <= 11 && idCaisse.matches("[a-zA-Z0-9]+");
}
    public static void main(String[] args) {
        String serverHost = args[0];
        int serverPort;
        Scanner scanner = new Scanner(System.in);
        String messageDeconnexion = "Vous avez été déconnecté.";
        if (args.length != 2) {
            logger.warning("Veuillez vous tenir à cette syntaxe suivante : java Client.java <adresse_ip_serveur> <numéro_de_port>");
            System.out.println("Veuillez vous tenir à cette syntaxe suivante : java Client.java <adresse_ip_serveur> <numéro_de_port>");
            return;
        }
        
        try {        
            serverPort = Integer.parseInt(args[1]);
        } catch (NumberFormatException e) {
            logger.log(Level.SEVERE, "Erreur: Le numéro de port doit être un nombre entier.", e);
            System.out.println("Erreur: Le numéro de port doit être un nombre entier.");
            return;
        }

        try (Socket socket = new Socket(serverHost, serverPort);
             PrintWriter out = new PrintWriter(socket.getOutputStream(), true);
             BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()))) {
            
            socket.setSoTimeout(TIMEOUT);

            logger.info("Entrez l'id de la caisse : ");
            System.out.println("Entrez l'id de la caisse : ");
            String numCaisse = scanner.nextLine();
            if (!estIdCaisseValide(numCaisse)) {
                logger.warning("ID de la caisse invalide (trop long ou contient des caractères spéciaux ou des valeurs nulles) vérif coté client .");
            System.out.println("ID de la caisse invalide (trop long ou contient des caractères spéciaux) vérif coté client .");
            return;  // Quitter si l'ID n'est pas valide
            }
            out.println(numCaisse);

            String reponseServeur = in.readLine();
            if (reponseServeur != null) {
                logger.info(reponseServeur);
                System.out.println(reponseServeur);

                if (reponseServeur.contains("Ce Terminal/Scanner n'appartient pas au CROUS")) {
                    return;
                }

                logger.info("Entrez votre ID client : ");
                System.out.println("Entrez votre ID client : ");
                
                String idClient = scanner.nextLine();
                if (!estIdClientValide(idClient)) { //vérification coté client avant d'envoyer la requete au serveur 
            System.out.println("ID client invalide (trop long ou contient des caractères spéciaux ou des valeurs nulles (vérif coté client)).");
            return;  // Quitter si l'ID n'est pas valide
            }
                out.println(idClient);

                String line;
                logger.info("Réponse du serveur :");
                System.out.println("Réponse du serveur :");
                
                boolean isMenuSection = false, isSupplementSection = false;
                while ((line = in.readLine()) != null) {
                    logger.info(line);
                    System.out.println(line);
                    

                    // Gérer les différentes sections de la communication
                    if (line.contains("Menu Izly:")) {
                        isMenuSection = true;
                    } else if (isMenuSection && line.contains("---- Fin de la liste des menus ----")) {
                        isMenuSection = false;
                        System.out.print("Veuillez sélectionner un menu (rentrer l'id en face du type du menu) : ");
                        String menuSelectionne = scanner.nextLine();
                        out.println(menuSelectionne);
                    } else if (line.contains("Avez-vous pris un supplement ?")) {
                        System.out.print("Veuillez répondre en tapant par : (oui/non) : ");
                        String reponseSupplement = scanner.nextLine();
                        out.println(reponseSupplement);
                        if (reponseSupplement.equalsIgnoreCase("oui")) {
                            isSupplementSection = true;
                        }
                    } else if (isSupplementSection && line.contains("---- Fin de la liste des suppléments ----")) {
                        System.out.print("Veuillez sélectionner un supplément (rentrer l'id en face du type du menu): ");
                        String supplementSelectionne = scanner.nextLine();
                        out.println(supplementSelectionne);
                        isSupplementSection = false;
                    }

                }
            } else {
                logger.warning("Aucune réponse reçue du serveur.");
                System.out.println("Aucune réponse reçue du serveur.");
                return;
            }
        } catch (ConnectException e) {
        System.out.println("Erreur de connexion : le serveur est peut-être hors ligne ou le port est fermé.");
        logger.log(Level.SEVERE, "Erreur de connexion", e);
        } catch (BindException e) {
        System.out.println("Erreur de liaison : le port est déjà utilisé sur la machine locale.");
        logger.log(Level.SEVERE, "Erreur de liaison", e);
        } catch (UnknownHostException e) {
        System.out.println("Erreur : l'adresse IP du serveur ou le nom DNS ne peut pas être résolu.");
        logger.log(Level.SEVERE, "Erreur de résolution d'hôte", e);    
        } catch (SocketException e) {
        logger.log(Level.SEVERE, "Une connexion établie a été abandonnée par un logiciel de votre ordinateur hôte");
        System.out.println("Une connexion établie a été abandonnée par un logiciel de votre ordinateur hôte");
        } catch (NumberFormatException e) {
        System.out.println("Le port doit être un nombre.");
        
        }catch (SocketTimeoutException e) {
            messageDeconnexion = "Déconnecté en raison du serveur ayant mis du temps à répondre.";
            logger.warning(messageDeconnexion);
            System.out.println(messageDeconnexion);
        } catch (IOException e) {
            messageDeconnexion = "Erreur de connexion : " + e.getMessage();
            logger.log(Level.SEVERE, messageDeconnexion, e);
            System.out.println(messageDeconnexion+e.getMessage());
        
        } finally {
            logger.info(messageDeconnexion);
            System.out.println(messageDeconnexion);

            scanner.nextLine();
        }
    }
}