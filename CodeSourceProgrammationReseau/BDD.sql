ALTER TABLE encaisser
ADD CONSTRAINT fk_encaisser_id_commande
FOREIGN KEY (num_caisse) REFERENCES caisse(num_caisse);
