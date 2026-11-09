# Installation et lancement

## 1. Prérequis

- Ouvrir un terminal intégré à VS Code : **Terminal → New Terminal**. Toutes les commandes ci-dessous s'exécutent dans ce
  terminal.

- Python 3.11 ou plus récent.

Cocher «Add python.exe to PATH» lors de l'installation. 

Pour vérifier que Python est installé, exécuter :
 
```powershell
py --version
```
Un numéro de version doit s'afficher (ex : `Python 3.11.4`).

## 2. Créer et activer l'environnement virtuel
 
**A la racine du projet**, exécuter :
 
```powershell
py -m venv venv
venv\Scripts\activate
```
*(macOS/Linux : `source venv/bin/activate`)*
 
Après activation, l'invite de commande doit afficher `(venv)` tout au
début de la ligne, par exemple :
```
(venv) PS C:\...\Optimisation Placement Rita 20260902>
```

Si l'erreur suivante apparaît :
```
Impossible de charger le fichier ...\venv\Scripts\Activate.ps1, car
l'exécution de scripts est désactivée sur ce système.
```
 
Exécuter cette commande :
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Taper `O` pour confirmer, puis relancer `venv\Scripts\activate`.
## 3. Installer les dépendances
 
Une fois `(venv)` visible dans l'invite, exécuter :
 
```powershell
py -m pip install -r requirements.txt
```

## 4. Lancer l'interface (Streamlit)

Depuis la racine du projet, exécuter :

```bash
streamlit run interface/interface_for_dispatch.py
```

Une page va s'ouvrir automatiquement dans le navigateur.

## 5. Modifier les paramètres figés de l'interface

S'il y a besoin de modifier certains paramètres figés (puissances min/max, coûts etc.), c'est possible depuis le fichier instances.py
