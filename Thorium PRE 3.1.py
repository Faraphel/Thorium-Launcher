LauncherVersion = "Pre 3.1"

import json, os, uuid, zipfile, urllib.request, traceback, subprocess, sys, ssl
from tkinter import *
from PIL import Image, ImageTk
from tkinter import ttk, messagebox, filedialog
from threading import Thread

SSL_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)

Libraries = [] # Liste de toutes les librairies à charger
GameDirectory = ".Thorium/" # Dossier du jeu
Texture = {} # Texture du launcher
ProfilUsed = {} # Dictionnaire utilisé pour lancer le jeu
AllProfil = {} # Liste de tous les profils chargés
Config = {} # Liste des options du launcher

HelpDownloadLink = "https://drive.google.com/uc?export=download&id=1AbmNzrkpY53DhBP51Uwjub1Hvo0oYeUf"
VersionDownloadLink = "https://drive.google.com/uc?export=download&id=1K5fnVWZer0A5HHYwDLPS166iK5l7QPbE"
try:
	Data = urllib.request.urlopen(context = SSL_context, url = HelpDownloadLink)
	with open("Help.json", "wb") as File: File.write(Data.read())
except: pass
try:
	with open("Help.json", "rb") as File: Help = json.load(File)
except: Help = {} # Donnée d'aide


def SaveConfig(event = None):
	Config["Option"] = {

		"Custom Args JVM": ProfilUsed["Custom Args JVM"].get(), # Ligne de code supplémentaire
		"RAM Min": ProfilUsed["RAM Min"].get(), # RAM Min
		"RAM Max": ProfilUsed["RAM Max"].get(), # RAM Max
		"Authentificate": ProfilUsed["Authentificate"].get(), # Activé l'authentification
		"RememberToken": ProfilUsed["RememberToken"].get(), # Se souvenir du token
		"UseOfficialLauncher": ProfilUsed["UseOfficialLauncher"].get(), # Va chercher dans les données du launcher officiel le token
		"Pseudo": ProfilUsed["Pseudo"].get(),
		"Logs": ProfilUsed["Logs"].get(),
	}

	Config["SelectProfil"] = SelectProfil.get()
	Config["FastServerIP"] = FastServerIP.get()

	with open("Config.json", "w") as File: File.write(json.dumps(Config))
def LoadConfig(event = None):
	global Config
	try:
		with open("Config.json", "r") as File: Config = json.load(File)

		for keys in list(Config["Option"].keys()):
			ProfilUsed[keys].set(Config["Option"][keys])

		SelectProfil.set(Config["SelectProfil"])
		FastServerIP.set(Config["FastServerIP"])
	except: print("Impossible de charger la config")
if not(os.path.exists(GameDirectory + "versions/")): os.makedirs(GameDirectory + "versions/")
if not(os.path.exists(GameDirectory + "launcher_profiles.json")):
	with open(GameDirectory + "launcher_profiles.json", "w") as File:
		File.write("""{
			"settings": {},
			"launcherVersion": {},
			"clientToken": "",
			"profiles": {},
			"analyticsFailcount": 0,
			"selectedUser": {},
			"analyticsToken": "",
			"selectedProfile": "",
			"authenticationDatabase": {}
			}""")# Crée le fichier launcher_profiles.json, nécéssaire pour installer Forge

def AssetsSearch(Version):
	if not(os.path.exists(GameDirectory + "versions/" + Version)): os.makedirs(GameDirectory + "versions/" + Version) # Crée un dossier s'il n'existe pas, sur la version désiré

	if not(os.path.exists(GameDirectory + "versions/{0}/{0}.json".format(Version))): # Vérifie si le fichier existe déjà
		LaunchStatut.config(text = "Téléchargement du fichier VersionManifest")
		try: VersionManifest = json.load(urllib.request.urlopen(context = SSL_context, url = "https://launchermeta.mojang.com/mc/game/version_manifest.json")) # Sinon va chercher le fichier contenant des informations sur des versions
		except: print(" | Impossible de télécharger le fichier VersionManifest")  # Log
		else: print(" | Succès !")

		for VersionInfo in VersionManifest["versions"]: # Cherche la séquence d'information correspondant à la version
			if VersionInfo["id"] == Version:
				VersionData = VersionInfo
				break
		with open(GameDirectory + "versions/{0}/{0}.json".format(Version), "wb") as File: # Télécharge le fichier
			LaunchStatut.config(text = "Téléchargement du fichier Version")
			try: File.write(urllib.request.urlopen(context = SSL_context, url = VersionData["url"]).read())
			except: print(" | Impossible de télécharger le fichier Version")  # Log
			else: print(" | Succès !")

	with open(GameDirectory + "versions/{0}/{0}.json".format(Version)) as JsonFile: # Charge le fichier Json
		Json = json.load(JsonFile)

	if not(os.path.exists(GameDirectory + "versions/{0}/{0}.jar".format(Version))): # Vérifie si le fichier .jar existe
		with open(GameDirectory + "versions/{0}/{0}.jar".format(Version), "wb") as File: # Télécharge le fichier
			LaunchStatut.config(text = "Téléchargement du fichier Client")
			try: File.write(urllib.request.urlopen(context = SSL_context, url = Json["downloads"]["client"]["url"]).read())
			except: print(" | Impossible de télécharger le fichier Client")  # Log
			else: print(" | Succès !")

	if list(Json.keys()).count("inheritsFrom") > 0: AssetsSearch(Json["inheritsFrom"]) # Si le fichier à une dépendance, la scan également
	else:
		if not(os.path.exists(GameDirectory + "assets/indexes/")): os.makedirs(GameDirectory + "assets/indexes/") # Crée un dossier pour les assets
		if not(os.path.exists(GameDirectory + "assets/indexes/%s.json" % Json["assetIndex"]["id"])): # Crée le fichier pour les assets
			LaunchStatut.config(text = "Téléchargement du fichier assetIndex")
			try: JsonAssets = urllib.request.urlopen(context = SSL_context, url = Json["assetIndex"]["url"]).read() # Va chercher le fichier contenant les assets
			except: print(" | Impossible de télécharger le fichier assetIndex")  # Log
			else: print(" | Succès !")

			with open(GameDirectory + "assets/indexes/%s.json" % Json["assetIndex"]["id"], "wb") as File: File.write(JsonAssets) # Sauvegarde de dossier des assets
		with open(GameDirectory + "assets/indexes/%s.json" % Json["assetIndex"]["id"]) as File: JsonAssets = json.load(File)

		for AssetsKeys in JsonAssets.keys(): # Fouille dans le fichier les assets
			for Assets in JsonAssets[AssetsKeys]:
				AssetsHash = JsonAssets[AssetsKeys][Assets]['hash']
				AssetsPrefix = AssetsHash[:2]

				if not(os.path.exists(GameDirectory + "assets/%s/%s" % (AssetsKeys, AssetsPrefix))): # Si le dossier n'existe pas,
					os.makedirs(GameDirectory + "assets/%s/%s" % (AssetsKeys, AssetsPrefix)) # le crée

				if not(os.path.exists(GameDirectory + "assets/%s/%s/%s" % (AssetsKeys, AssetsPrefix, AssetsHash))): # Si le fichier n'existe pas,
					with open(GameDirectory + "assets/%s/%s/%s" % (AssetsKeys, AssetsPrefix, AssetsHash), 'wb') as File: # Le crée
						LaunchStatut.config(text = "Téléchargement de l'asset : " + Assets)
						try: File.write(urllib.request.urlopen(context = SSL_context, url = "http://resources.download.minecraft.net/%s/%s" % (AssetsPrefix, AssetsHash)).read()) # Téléchargement
						except: print(" | Impossible de télécharger l'asset : " + Assets)  # Log
						else: print(" | Succès !")
def LibrariesSearch(JsonFile):
	with open(JsonFile, "rb") as JsonFile: Json = json.load(JsonFile) # Charge le fichier Json

	for Lib in Json["libraries"]: # Recherche toutes les librairies noté à l'intérieur
		ActualLib = Lib.copy() # Sert à faire une recherche approfondie
		while True:
			try:
				package, name, version = ActualLib["name"].split(':') # Convertie le nom en lien de fichier
				EchecLibUrl = "{0}/{1}/{2}/{1}-{2}.jar".format(package.replace('.', '/'), name, version)
				LibPath = "libraries/" + EchecLibUrl
				Libraries.append(LibPath) # Ajoute la librairies à la liste des librairies total

				if not(os.path.exists(GameDirectory + LibPath)): # Vérifie l'existence de la librairie (classique)
					if not(os.path.exists(os.path.dirname(GameDirectory + LibPath))): os.makedirs(os.path.dirname(GameDirectory + LibPath))
					with open(GameDirectory + LibPath, "wb") as LibFile: # Sinon la télécharge

						try:
							LaunchStatut.config(text = "Téléchargement du fichier : " + ActualLib["name"]) # Log
							Download = urllib.request.urlopen(context = SSL_context, url = ActualLib["downloads"]["artifact"]["url"]).read()
							LibFile.write(Download) # Téléchargement

						except:
							try:
								print(" | -> Téléchargement du fichier (sans echec)")
								Download = urllib.request.urlopen(context = SSL_context, url = "https://libraries.minecraft.net/" + EchecLibUrl).read()
								LibFile.write(Download)
							except:
								print(" | Impossible de télécharger la librairie (classique) : " + LibPath + "\n | (Vérifier si Forge est bien installé)") # Log
							else:
								print(" |")
						else: print(" | Succès !")


				if list(ActualLib.keys()).count("natives") > 0: # Vérifie que le fichier Json contient une information sur les "natives"
					if list(ActualLib['natives'].keys()).count("windows") > 0: # Si le fichier contient une donnée "natives" à propos de l'OS "windows"

						Native = ActualLib["natives"]["windows"].replace('${arch}', "64") # Recherche une librairies contenant les natives
						rlPath = "{0}/{1}/{2}/{1}-{2}-{3}.jar".format(package.replace('.', '/'), name, version, Native) # Crée un lien vers ces librairies
						rPath = "libraries/" + rlPath # Le rl est plus utile au téléchargement, le r est plus utile au chemin uri
						LibRep = ActualLib.get('url', 'https://libraries.minecraft.net/')

						try:
							if not(os.path.exists(GameDirectory + rPath)): # Vérifie l'existence de la librairie (native)
								if not(os.path.exists(os.path.dirname(GameDirectory + rPath))): os.makedirs(os.path.dirname(GameDirectory + rPath))
								with open(GameDirectory + rPath, "wb") as LibFile: # Sinon la télécharge

									LaunchStatut.config(text = "Téléchargement du fichier : " + Native) # Log
									try: LibFile.write(urllib.request.urlopen(context = SSL_context, url = LibRep + rlPath).read()) # Téléchargement
									except: print(" | Impossible de télécharger la librairie (native) %s" % str(LibPath)) # Log
									else: print(" | Succès !")

							with zipfile.ZipFile(GameDirectory + rPath, 'r') as LibFile: # Extrait les natives de ces librairies
								for name in LibFile.namelist():
									if not (name.startswith('META-INF') or name.startswith('.')): LibFile.extract(name, GameDirectory + 'natives')

						except zipfile.BadZipFile:
							print("Erreur pour l'extraction de : " + LibPath) # Si le fichier est corrompu, il est évité
							os.remove(GameDirectory + rPath)

			except Exception as e:
				print("Erreur : " + traceback.format_exc()) # En cas d'erreur, log le nom de la librairies problématique
				if list(ActualLib.keys()).count("downloads") > 0: ActualLib = ActualLib["downloads"] # Recommence la cherche en allant plus loin dans les données
				elif list(ActualLib.keys()).count("artifact") > 0: ActualLib = ActualLib["artifact"]
				else:
					print("Impossible d'aller plus loin /!\\ : " + str(ActualLib))
					break
			else:
				break # Passe à la librairie suivante


	if list(Json.keys()).count("inheritsFrom") > 0: # Vérifie une dépendance ( utilisé par Forge )
		return LibrariesSearch(GameDirectory + "versions/{0}/{0}.json".format(Json["jar"])) # Fonction récursif pour la dépendance
	else:
		if list(Json.keys()).count("assetIndex"): AssetIndex = Json["assetIndex"]["id"]
		return AssetIndex

Fen = Tk()

ScreenWidth = Fen.winfo_screenwidth()
ScreenHeight = Fen.winfo_screenheight()

Fen.title(u"Thorium λ (%s)" % LauncherVersion)
if os.path.exists("icon.ico"): Fen.iconbitmap("icon.ico")
Fen.resizable(width=False, height=False)
Fen.columnconfigure(0, weight = 1)

def LoadTexture(Path = "LauncherTexture.zip"):
	if os.path.exists(Path):
		with zipfile.ZipFile(Path) as File:
			for Name in File.namelist():
				File.extract(Name, "tempTexture")
				Texture[Name] = ImageTk.PhotoImage(Image.open("tempTexture/" + Name))

	else:
		messagebox.showerror("Erreur", "Impossible de charger les textures")
LoadTexture()

def ShowMenu(SelectMenu = "MainMenu"):
	for _Menu, MenuWidget in Menu.items(): MenuWidget.grid_forget()
	Menu[SelectMenu].grid(row = 1, column = 1)

Menu = {} # Liste contenant tout les widget "Menu", sert a changer de menu plus facilement
Menu["MainMenu"] = Frame(Fen) # Menu Principal
ShowMenu()

NewsDisplayScroll = Scrollbar(Menu["MainMenu"], orient = VERTICAL) # Scrollbar des nouveautés
NewsDisplayScroll.grid(row = 1, column = 3, sticky = "NSW")
NewsDisplay = Canvas(Menu["MainMenu"], yscrollcommand = NewsDisplayScroll.set, scrollregion = (0, 0, 300, 800), width = ScreenWidth / 3, height = ScreenHeight / 3) # Display des nouveautés
NewsDisplay.grid(row = 1, column = 1, sticky = "NEWS", columnspan = 2)
NewsDisplayScroll.config(command = NewsDisplay.yview) # Configuration pour bind la Scrollbar au Canvas

Fastbar = LabelFrame(Menu["MainMenu"], text = "Lancement") # Barre inférieur qui permet d'afficher les options de lancement
Fastbar.grid(row = 4, column = 1)

Label(Fastbar, text = "Profil :").grid(row = 1, column = 1, rowspan = 2)
SelectProfil = StringVar() # Sélection du profil
ProfilBox = ttk.Combobox(Fastbar, value = AllProfil, textvariable = SelectProfil)
ProfilBox.grid(row = 1, column = 2, rowspan = 2)
ProfilBox.bind("<<ComboboxSelected>>", SaveConfig)

Label(Fastbar, text = " Pseudo / Email :").grid(row = 1, column = 3, padx = 5)
Label(Fastbar, text = " Mot De Passe :").grid(row = 2, column = 3, padx = 5)
ProfilUsed["Pseudo"] = StringVar(value = "ThoriumPlayer")
ProfilUsed["Password"] = StringVar()
PseudoBox = Entry(Fastbar, textvariable = ProfilUsed["Pseudo"])
PseudoBox.grid(row = 1, column = 4)
PasswordBox = Entry(Fastbar, show = "*", textvariable = ProfilUsed["Password"])
PasswordBox.grid(row = 2, column = 4)

def Auth(Email, password):
	try:
		print("- Authentification par défaut")
		if ProfilUsed["Authentificate"].get():
			data = {'agent': {'name': 'Minecraft', 'version': 1}, 'username': Email,
			   'password': password}
			req = urllib.request.Request(url='https://authserver.mojang.com/authenticate', data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
			jsonData = json.loads(urllib.request.urlopen(context = SSL_context, url = req).read())
			Pseudo = jsonData['selectedProfile']['name']
			Token = jsonData['accessToken']
			UUID = jsonData['selectedProfile']['id']

			if ProfilUsed["RememberToken"].get():
				Config["Authentification"] = {"Pseudo": Pseudo, "Token": Token, "UUID": UUID}

			return(Pseudo, Token, UUID, False) # Pseudo, Token, UUID & Erreur ?
		else: raise Exception

	except:
		try:
			print("- Authentification par souvenir")
			if list(Config.keys()).count("Authentification") > 0 and ProfilUsed["RememberToken"].get():
				messagebox.showwarning("Attention", "L'authentification à échoué. Tentative avec des données antérieures...") # Authentification par donnée antérieure
				return(Config["Authentification"]["Pseudo"], Config["Authentification"]["Token"], Config["Authentification"]["UUID"], False)
			else: raise Exception
		except:
			try:
				print("- Authentification par launcher officiel")
				if ProfilUsed["UseOfficialLauncher"].get():
					with open('%s\\AppData\\Roaming\\.minecraft\\launcher_profiles.json' % os.getenv('HOME'), "r") as File:
						OfficialLauncherData = json.load(File)

					AuthData = OfficialLauncherData['authenticationDatabase'][list(OfficialLauncherData['authenticationDatabase'].keys())[0]] # Authentification par le launcher officiel
					UUID = list(AuthData['profiles'].keys())[0]
					Pseudo, Token = AuthData['profiles'][profile_id]['displayName'], AuthData['accessToken']

					return(Pseudo, Token, UUID, False)
				else: raise Exception
			except:
				print("- Authentification en mode Echec")
				return(Email, "ERROR", str(uuid.uuid3(type('', (), dict(bytes=b''))(), ProfilUsed["Pseudo"].get())), True)
def LaunchGame(Profil):
	CancelStartGame = False # Dans le cas ou une erreur survient, l'utilisateur peut être mener à annuler le lancement du jeu.

	LaunchProgress["value"] = 1
	LaunchStatut.config(text = "Authentification") # Log
	Pseudo, Token, UUID, AuthSuccess = Auth(ProfilUsed["Pseudo"].get(), ProfilUsed["Password"].get())
	if AuthSuccess and ProfilUsed["Authentificate"].get():
		if not(messagebox.askyesno("Erreur", "Impossible de s'authentifier. Voulez-vous lancer le jeu en version offline ?")): CancelStartGame = True

	LaunchProgress["value"] = 2
	if not(Profil["ZipFileInstalled"]) and not(CancelStartGame): # Si les fichiers
		try:
			for ZipFile in Profil["AddZipFile"]:
				LaunchStatut.config(text = "Téléchargement des fichiers additionnels... (Peut être long !)") # Log
				if ZipFile != "":
					with open("AdditionnalFile.temp", "wb") as File:
						File.write(urllib.request.urlopen(context = SSL_context, url = ZipFile).read())

					with zipfile.ZipFile("AdditionnalFile.temp") as File:
						File.extractall(GameDirectory + Profil["DirectoryFile"])
		except Exception as e:
			if not(messagebox.askyesno("Erreur", "Une erreur est survenue pendant le téléchargement des fichiers additionnels.\
				Souhaitez vous vraiment lancer le jeu ? (Ceci peut engendrer des dysfonctionnements !)\n\n\n\n" + str(e))):
				CancelStartGame = True

	if not(CancelStartGame):
		global CmdLine

		CmdLine = "java -Djava.library.path=natives " # Ligne de commande de lancement
		CmdLine += "-Xmn%iM -Xmx%iM " % (ProfilUsed["RAM Min"].get(), ProfilUsed["RAM Max"].get())
		JsonPath = GameDirectory + r"versions/{0}/{0}.json".format(Profil["Json"]) # Lien uri du fichier Json

		if os.path.exists(JsonPath): # Vérifie si le fichier .json existe
			with open(JsonPath, "rb") as JsonFile: JsonFile = json.load(JsonFile)
			if list(JsonFile.keys()).count("jar") > 0: VersionName = JsonFile["jar"] # Si le Json n'est pas officiel, prend la version du .jar

			else: VersionName = JsonPath.split("/")[-2] # Sinon, utilise le nom du chemin pour déterminer la version
		else: VersionName = JsonPath.split("/")[-2]
		AssetIndex = VersionName # Sert à initialiser la valeur de l'AssetIndex, qui est actualiser dans LibrariesSearch

		LaunchProgress["value"] = 3
		LaunchStatut.config(text = "Recherche d'assets") # Log
		AssetsSearch(VersionName) # Rafraichi les Assets

		LaunchProgress["value"] = 4
		LaunchStatut.config(text = "Recherche de librairies") # Log
		AssetIndex = LibrariesSearch(JsonPath) # Rafraichi les Librairies, et détermine également la valeur "AssetIndex"

		LaunchProgress["value"] = 5
		LaunchStatut.config(text = "Lancement du jeu") # Log
		with open(JsonPath, "rb") as JsonFile: JsonFile = json.load(JsonFile)
		ReplaceValue = {"${auth_player_name}": Pseudo, # Valeur à remplacer dans la ligne de commande
						"${version_name}": VersionName, # Nom de la version
						"${game_directory}": Profil["DirectoryFile"], # Dossier du jeu, déjà placer dans la commande avec le "cd GameDirectory"
						"${assets_root}": "assets", # Dossier des assets
						"${assets_index_name}": AssetIndex, # Sous dossier des assets
						"${auth_uuid}": UUID, # uuid (ici, offline)
						"${auth_access_token}": Token, # Token d'accès (pour compte officiel)
						"${user_type}": "Forge", # Je sais pas a quoi sa sert
						"${version_type}": "\"Thorium - Par Raphael60650\"", # Le message ici est customisable :)
						"${user_properties}": "{}"}

		CmdLine += "-cp \"%s\" %s " % (";".join(Libraries) + ";versions\\{0}\\{0}.jar".format(VersionName), JsonFile["mainClass"]) # Formatage de la ligne de commande
		try: CmdLine += JsonFile["minecraftArguments"] # Dans la majorité des fichiers .json
		except: CmdLine += " ".join([part for part in JsonFile["arguments"]["game"] if type(part) == str]) # .json comme celui de la 1.13

		for Old in ReplaceValue.keys():
			print("Java JVM : " + str(Old) + " -> " + str(ReplaceValue[Old]))
			CmdLine = CmdLine.replace(Old, str(ReplaceValue[Old])) # Remplacement des valeurs de ReplaceValue

		print(CmdLine) # Log la ligne de commande
		GameProcess = subprocess.Popen("cd %s && %s" % (GameDirectory, CmdLine), shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE) # Lance le jeu

		SaveConfig()
		if ProfilUsed["Logs"].get():

			LogsFen = Toplevel()
			try: LogsFen.iconbitmap("icon.ico")
			except: pass
			LogsText = Text(LogsFen)
			LogsText.grid(row = 1, column = 1, sticky = "NEWS")

			def RefreshLog():
				while not(GameProcess.poll()): # Tant que le jeu n'est pas fermé
					for Line in GameProcess.stdout: LogsText.insert(END, Line) # Ligne normal
					for Line in GameProcess.stderr: LogsText.insert(END, Line) # Ligne d'erreur
					LogsText.see(END)

				LogsFen.after(10, RefreshLog)

			RefreshLog()

	LaunchProgress["value"] = 0
	LaunchStatut.config(text = "") # Log


LaunchStatut = Label(Menu["MainMenu"], text = "")
LaunchStatut.grid(row = 2, column = 1, columnspan = 2)

LaunchProgress = ttk.Progressbar(Menu["MainMenu"], orient = HORIZONTAL, maximum = 5) # Barre de chargement
LaunchProgress.grid(row = 3, column = 1, columnspan = 2, sticky = "NEWS")

Button(Fastbar, text = "Démarrer", relief = RIDGE, command = lambda: Thread(target = lambda: LaunchGame(AllProfil[SelectProfil.get()])).start()).grid(row = 3, column = 1, columnspan = 3, sticky = "NEWS") # Bouton pour lancer le jeu
Button(Fastbar, text = "Options", relief = RIDGE, command = lambda: ShowMenu("Option")).grid(row = 3, column = 4, sticky = "NEWS") # Bouton d'accès au menu des options


FastServerInfo = LabelFrame(Menu["MainMenu"], text = "Serveur")
FastServerInfo.grid(row = 4, column = 2, rowspan = 2, sticky = "NEWS")
FastServerIP = StringVar(value = "Thorium.omgcraft.fr")
FastServerEntry = Entry(FastServerInfo, textvariable = FastServerIP)
FastServerEntry.grid(row = 1, column = 1)

ServerStatut = Label(FastServerInfo, text = "", font = ("Purisa", 10))
ServerStatut.grid(row = 2, column = 1, sticky = "WE")

ServerPlayer = Label(FastServerInfo, text = "0 / 0", font = ("Purisa", 10))
ServerPlayer.grid(row = 3, column = 1, sticky = "WE")

try:
	import mcquery
	def RefreshFastServer():
		query = mcquery.MineStat(FastServerIP.get(), 15040)

		if query.online:
			ServerStatut.config(text = "Ouvert", fg = "green")
			ServerPlayer.config(text = str(query.current_players) + " / " + str(query.max_players))
		else: ServerStatut.config(text = "Fermé", fg = "red")

		Fen.after(1000, RefreshFastServer)
	RefreshFastServer()
except: pass


def RefreshNews():
	NewsDisplay.create_rectangle(0, 0, 1000, 1000, fill = "green")
	NewsDisplay.create_image(0, 0, image = Texture["th_background.png"])
	NewsDisplay.create_image(NewsDisplay.winfo_width() // 2, NewsDisplay.winfo_height() // 2, image = Texture["th_title.png"])# Sert a faire le rendu sur le canvas dans le menu principal, appelé juste avant le mainloop()

####################################################################################################
####################################################################################################

Menu["Option"] = Frame(Fen)
ExperimentSection = LabelFrame(Menu["Option"], text = "Expérimenté") # Section pour les paramètres destinés aux joueurs expérimentés
ExperimentSection.grid(row = 1, column = 1, sticky = "NEWS")

ProfilUsed["Custom Args JVM"] = StringVar() # Ligne de code supplémentaire
ProfilUsed["RAM Min"] = IntVar(value = 1024) # RAM Min
ProfilUsed["RAM Max"] = IntVar(value = 2048) # RAM Max
ProfilUsed["Logs"] = IntVar(value = 0)

Label(ExperimentSection, text = "Args JVM :").grid(row = 1, column = 1)
CustomArgsJVMEntry = Entry(ExperimentSection, textvariable = ProfilUsed["Custom Args JVM"])
CustomArgsJVMEntry.grid(row = 1, column = 2, sticky = "NEWS")
CustomArgsJVMEntry.bind("<Key>", SaveConfig)

Label(ExperimentSection, text = "RAM Minimum (Mo) :").grid(row = 2, column = 1)
RAMMinSpinbox = Spinbox(ExperimentSection, from_ = 1, to = 2**32, textvariable = ProfilUsed["RAM Min"], command = SaveConfig)
RAMMinSpinbox.grid(row = 2, column = 2, sticky = "NEWS")

Label(ExperimentSection, text = "RAM Maximum (Mo) :").grid(row = 3, column = 1)
RAMMaxSpinbox = Spinbox(ExperimentSection, from_ = 1, to = 2**32, textvariable = ProfilUsed["RAM Max"], command = SaveConfig)
RAMMaxSpinbox.grid(row = 3, column = 2, sticky = "NEWS")

Checkbutton(ExperimentSection, text = "Activer les logs", variable = ProfilUsed["Logs"], command = SaveConfig).grid(row = 4, column = 1, columnspan = 2)

####################################################################################################

AuthentificationSection = LabelFrame(Menu["Option"], text = "Authentification") # Menu des options à propos de l'authentification
AuthentificationSection.grid(row = 2, column = 1, sticky = "NEWS")

ProfilUsed["Authentificate"] = IntVar(value = 1) # Activé l'authentification
ProfilUsed["RememberToken"] = IntVar(value = 1) # Se souvenir du token
ProfilUsed["UseOfficialLauncher"] = IntVar(value = 0) # Va chercher dans les données du launcher officiel le token
Checkbutton(AuthentificationSection, text = "Authentification", variable = ProfilUsed["Authentificate"], command = SaveConfig).grid(row = 1, column = 1, sticky="W")
Checkbutton(AuthentificationSection, text = "Se souvenir du Token", variable = ProfilUsed["RememberToken"], command = SaveConfig).grid(row = 2, column = 1, sticky="W")
Checkbutton(AuthentificationSection, text = "Identification via \nle Launcher Officiel", variable = ProfilUsed["UseOfficialLauncher"], command = SaveConfig).grid(row = 3, column = 1, sticky="W")

AuthTestLabel = Label(AuthentificationSection, text = "")
AuthTestLabel.grid(row = 5, column = 1)
def TestAuth():
	Pseudo, Token, UUID, AuthSuccess = Auth(ProfilUsed["Pseudo"].get(), ProfilUsed["Password"].get())
	AuthTestLabel.config(text = "Pseudo : %s \nUUID : %s \nAuthentification : %s" % (Pseudo, UUID, str(AuthSuccess).replace("True", "Echec").replace("False", "Réussi")))

Button(AuthentificationSection, text = "Tester l'authentification", command = TestAuth, relief = RIDGE).grid(row = 4, column = 1, sticky = "NEWS")

####################################################################################################

ModSection = LabelFrame(Menu["Option"], text = "Mod") # Menu des options à propos des mods
ModSection.grid(row = 1, column = 2, rowspan = 2)

MetaDataModList = Label(ModSection)
MetaDataModList.grid(row = 5, column = 1, columnspan = 3)

ModSearchPath = StringVar(value = GameDirectory) # Variable qui contient le chemin du jeu
Entry(ModSection, textvariable = ModSearchPath).grid(row = 1, column = 1, sticky = "NSE")

ModListbox = Listbox(ModSection, width = 50)
ModListbox.grid(row = 2, column = 1, columnspan = 2, rowspan = 2, sticky = "NEWS")

def SelectModSearchPath(Path = "", Silent = False):
	MetaData = "("

	if not(Path): Path = filedialog.askdirectory() # Demande un dossier a fouiller
	if os.path.exists(Path): # S'il existe,
		if os.path.exists(Path + "/mods"): # Si un dossier mod existe à l'interieur,
			if len(os.listdir(Path + "/mods")) > 0:
				ModListbox.delete(0, END)
				ModListDir = os.listdir(Path + "/mods")
				MetaData += "mods : " + str(len(ModListDir)) + " | "

				for mods in ModListDir:
					ModListbox.insert(END, mods) # fouille et insert les mods dans la liste
					ModListbox.itemconfig(END, fg = "green")
				ModSearchPath.set(Path) # Initialise une variable
			else:
				if not(Silent): messagebox.showerror("Erreur", "Le dossier sélectioné ne contient aucun mod")
		else:
			if not(Silent): messagebox.showerror("Erreur", "Le dossier de mod n'existe pas, veuillez lancer au moins une fois le jeu")
		if os.path.exists(Path + "/disableMods"): # Fouille dans le dossier des mods désactivé
			DisableModListDir = os.listdir(Path + "/disableMods")
			MetaData += "mods désactivés : " + str(len(DisableModListDir))

			for mods in DisableModListDir:
				ModListbox.insert(END, mods)
				ModListbox.itemconfig(END, fg = "gray")
		else: os.makedirs(Path + "/disableMods") # S'il n'existe pas, le crée
	else:
		if not(Silent): messagebox.showerror("Erreur", "Ce dossier n'existe pas")

	MetaData += ")"
	MetaDataModList.config(text = MetaData)
SelectModSearchPath(GameDirectory, True) # Fait une recherche par défaut pour chercher les mods dans le dossier

Button(ModSection, text = "C:/", command = SelectModSearchPath, relief = RIDGE).grid(row = 1, column = 2, sticky = "W") # Entry où entrer le lien ou chercher les mods

Button(ModSection, text = "Ouvrir", command = lambda: subprocess.Popen("explorer.exe " + os.path.abspath(ModSearchPath.get()) + "mods/", shell = True), relief = RIDGE).grid(row = 1, column = 3, sticky = "NEWS") # Bouton ouvrant un dossier vers le dossier de mods

Label(ModSection, text = "Mod Installé", fg = "green").grid(row = 2, column = 3)
Label(ModSection, text = "Mod Désactivé", fg = "gray").grid(row = 3, column = 3)

ModActionButton = Button(ModSection, text = "---------", relief = RIDGE, fg = "gray") # Bouton destiné à activé / désactivé les mods
ModActionButton.grid(row = 4, column = 1, columnspan = 2, sticky = "NEWS")
def ModListboxSelect(event):
	def DisableModList(ModName):
		os.rename(ModSearchPath.get() + "/mods/" + ModName, ModSearchPath.get() + "/disableMods/" + ModName)
		SelectModSearchPath(ModSearchPath.get())

	def EnableModList(ModName):
		os.rename(ModSearchPath.get() + "/disableMods/" + ModName, ModSearchPath.get() + "/mods/" + ModName)
		SelectModSearchPath(ModSearchPath.get())

	Index = ModListbox.curselection()[-1]
	ModName = ModListbox.get(Index)
	if os.listdir(ModSearchPath.get() + "/mods").count(ModName) > 0: ModActionButton.config(text = "Désactivé", fg = "red", command = lambda: DisableModList(ModName))
	elif os.listdir(ModSearchPath.get() + "/disableMods").count(ModName) > 0: ModActionButton.config(text = "Activé", fg = "green", command = lambda: EnableModList(ModName))
ModListbox.bind('<<ListboxSelect>>', ModListboxSelect)

####################################################################################################

ProfilSection = LabelFrame(Menu["Option"], text = "Profil") # Menu des options à propos des mods
ProfilSection.grid(row = 1, column = 3, rowspan = 2)

def RefreshEditOption(event = None):
	try: ProfilEditButton.config(fg = "black", command = lambda: ActionProfil(ProfilListbox.get(ProfilListbox.curselection()[-1])))
	except: ProfilEditButton.config(fg = "gray", command = lambda: "pass")


ProfilListbox = Listbox(ProfilSection)
ProfilListbox.grid(row = 1, column = 1, columnspan = 2)
ProfilListbox.bind("<<ListboxSelect>>", RefreshEditOption)

def ActionProfil(Profil = ""):
	ShowMenu("ActionProfil")
	if Profil:
		ProfilName.set(Profil)
		SelectVersion.set(AllProfil[Profil]["Json"])
		AddZipFile.set(";".join(AllProfil[Profil]["AddZipFile"]))
		DirectoryFile.set(AllProfil[Profil]["DirectoryFile"])

		VersionListbox.select_set(VersionListbox.get(0, END).index(SelectVersion.get())) # Sélectionne le nom de la version
		VersionListboxSelect(None)


Button(ProfilSection, text = "Nouveau", relief = RIDGE, command = ActionProfil).grid(row = 2, column = 1, sticky = "WE")
ProfilEditButton = Button(ProfilSection, text = "Modifier", relief = RIDGE, fg = "gray")
ProfilEditButton.grid(row = 2, column = 2, sticky = "WE")

Button(Menu["Option"], text = "Aide", command = lambda: ShowMenu("Help"), relief = RIDGE).grid(row = 10, column = 1, sticky = "W")
Button(Menu["Option"], text = "Menu Principal", command = lambda: ShowMenu("MainMenu"), relief = RIDGE).grid(row = 10, column = 1, columnspan = 10, sticky = "E")

####################################################################################################
####################################################################################################

Menu["ActionProfil"] = Frame(Fen)

VersionList = {} # Dictionnaire qui contient les versions
ProfilName = StringVar(value = "Nouveau Profil") # Nom du profil
SelectVersion = StringVar() # Version sélectionné
AddZipFile = StringVar() # Archive à télécharger et dézipper
DirectoryFile = StringVar(value = ".") # Dossier dans lequel executé le jeu

def VersionListRefresh():
	for Version in os.listdir(GameDirectory + "versions/"):
		JsonPath = GameDirectory + "versions/{0}/{0}.json".format(Version)
		if os.path.exists(JsonPath):
			VersionList[Version] = {}
			VersionList[Version]["Json"] = Version # Version du jeu, utilisé pour le lien du .json
			VersionList[Version]["Type"] = "Unknown" # Par défaut, la version est inconnu
			VersionList[Version]["Install"] = True # Check si la version est déjà installer

	try: VersionManifest = json.load(urllib.request.urlopen(context = SSL_context, url = "https://launchermeta.mojang.com/mc/game/version_manifest.json")) # Sinon va chercher le fichier contenant des informations sur des versions
	except: print(" | Impossible de télécharger le fichier VersionManifest")  # Log
	else:
		print(" | Succès !")
		for VersionData in VersionManifest["versions"]:
			if list(VersionList.keys()).count(VersionData["id"]) == 0:
				VersionList[VersionData["id"]] = {}
				VersionList[VersionData["id"]]["Json"] = VersionData["id"] # Version du jeu, utilisé pour le lien du .json
				VersionList[VersionData["id"]]["Type"] = VersionData["type"] # Type de la version
				VersionList[VersionData["id"]]["Install"] = False
			else:
				VersionList[VersionData["id"]]["Type"] = VersionData["type"] # Met à jour "l'inconnu" plus haut

	VersionListbox.delete(0, END)
	for VersionData in VersionList:
		VersionListbox.insert(END, VersionList[VersionData]["Json"])
		if VersionList[VersionData]["Type"] == "snapshot": VersionListbox.itemconfig(END, bg = "purple", fg = "white")
		elif VersionList[VersionData]["Type"] == "release": VersionListbox.itemconfig(END, bg = "cyan")
		elif VersionList[VersionData]["Type"] == "old_beta": VersionListbox.itemconfig(END, bg = "darkgray")
		elif VersionList[VersionData]["Type"] == "old_alpha": VersionListbox.itemconfig(END, bg = "gray")
		else: VersionListbox.itemconfig(END, bg = "gold")

		if VersionList[VersionData]["Install"]: VersionListbox.itemconfig(END, fg = "blue") # Si la version est déjà installé
def VersionListboxSelect(event):
	Index = VersionListbox.curselection()[-1]
	Name = VersionListbox.get(Index)
	SelectVersion.set(Name)
	LabelSelectVersion.config(text = Name)


Label(Menu["ActionProfil"], text = "Nom :").grid(row = 1, column = 1)
Entry(Menu["ActionProfil"], textvariable = ProfilName).grid(row = 1, column = 2, sticky = "WE") # Nom du profil

VersionListbox = Listbox(Menu["ActionProfil"])
VersionListbox.grid(row = 2, column = 1, columnspan = 2, sticky = "NEWS") # Liste des versions
LabelSelectVersion = Label(Menu["ActionProfil"], text = "Version : Aucune")
LabelSelectVersion.grid(row = 3, column = 1, columnspan = 2)
VersionListbox.bind('<<ListboxSelect>>', VersionListboxSelect)

HelpVersionTypeFrame = LabelFrame(Menu["ActionProfil"], text = "Type")
HelpVersionTypeFrame.grid(row = 2, column = 3)
Label(HelpVersionTypeFrame, text = "Release", bg = "cyan").grid(row = 1, column = 1, sticky = "WE")
Label(HelpVersionTypeFrame, text = "Snapshot", bg = "purple", fg = "white").grid(row = 2, column = 1, sticky = "WE")
Label(HelpVersionTypeFrame, text = "Beta", bg = "darkgray").grid(row = 3, column = 1, sticky = "WE")
Label(HelpVersionTypeFrame, text = "Beta", bg = "gray").grid(row = 4, column = 1, sticky = "WE")
Label(HelpVersionTypeFrame, text = "Inconnu", bg = "gold").grid(row = 5, column = 1, sticky = "WE")
Label(HelpVersionTypeFrame, text = "Installé", fg = "blue").grid(row = 6, column = 1, sticky = "WE", pady = 5)

Label(Menu["ActionProfil"], text = "Archive additionnel :").grid(row = 4, column = 1)
Entry(Menu["ActionProfil"], textvariable = AddZipFile).grid(row = 4, column = 2, sticky = "WE") # Archive additionnel à télécharger

Label(Menu["ActionProfil"], text = "Dossier de jeu :").grid(row = 5, column = 1)
Entry(Menu["ActionProfil"], textvariable = DirectoryFile).grid(row = 5, column = 2, sticky = "WE") # Dossier de jeu
Button(Menu["ActionProfil"], text = "...", relief = RIDGE, command = lambda: DirectoryFile.set(filedialog.askopenfilenames())).grid(row = 5, column = 3, sticky = "W")

def RefreshVersionList():
	ProfilBox.config(values = list(AllProfil.keys())) # Actualise la liste des profil dans le menu principal

	ProfilListbox.delete(0, END)
	for ProfilData in AllProfil:
		ProfilListbox.insert(END, ProfilData)

def SaveProfil():
	EditedProfil = {}
	EditedProfil["Json"] = SelectVersion.get()
	EditedProfil["AddZipFile"] = AddZipFile.get().split(";")
	EditedProfil["DirectoryFile"] = DirectoryFile.get()
	EditedProfil["ZipFileInstalled"] = False

	if ProfilName.get(): # Vérifie si un nom de profil à été saisi
		if list(AllProfil.keys()).count(ProfilName.get()) != 0: # Vérifie s'il existe déjà :
			if not(messagebox.askyesno("Attention", "Voulez-vous remplacer le profil %s ?" % ProfilName.get())):
				return # Stop la fonction

		AllProfil[ProfilName.get()] = EditedProfil.copy() # Si oui l'inclue dans tout les profils chargés

		RefreshVersionList() # Actualise les listes de versions
		ShowMenu("Option") # Affiche le menu des options

		if os.path.exists("Profil.json.backup"): os.remove("Profil.json.backup")
		if os.path.exists("Profil.json"): os.rename("Profil.json", "Profil.json.backup")
		with open("Profil.json", "w") as File: json.dump(AllProfil, File)

	else: messagebox.showerror("Erreur", "Veuillez entrer un nom de profil")
def DeleteProfil():
	if messagebox.askyesno("Attention", "Souhaitez-vous vraiment effacer ce profil ? (%s)" % ProfilName.get()):
		if list(AllProfil.keys()).count(ProfilName.get()) > 0: # Dans le cas où l'utilisateur quitte par la sauvegarde
			AllProfil.pop(ProfilName.get())
			with open("Profil.json", "w") as File: json.dump(AllProfil, File)
			messagebox.showinfo("", "Profil effacé")

		try: SelectProfil.set(list(AllProfil.keys())[-1])
		except: pass

		RefreshVersionList()
		RefreshEditOption() # Actualise le bouton d'édition
		ShowMenu("Option")
def AskOptionMenu():
	if messagebox.askyesno("Attention", "Souhaitez-vous quitter sans sauvegarder ?"): ShowMenu("Option")

Button(Menu["ActionProfil"], text = "Sauvegarder", command = SaveProfil, relief = RIDGE).grid(row = 10, column = 1, sticky = "WS", pady = 5)
Button(Menu["ActionProfil"], text = "Effacer", command = DeleteProfil, relief = RIDGE).grid(row = 10, column = 2, columnspan = 9, sticky = "WS", pady = 5)
Button(Menu["ActionProfil"], text = "Retour", command = AskOptionMenu, relief = RIDGE).grid(row = 10, column = 2, columnspan = 10, sticky = "ES", pady = 5)

VersionListRefresh()

####################################################################################################
####################################################################################################

Menu["Help"] = Frame(Fen)

def HelpRefresh(event = None):
	try: HelpText.delete("0.0", END)
	except: pass
	HelpText.insert(END, Help[HelpListbox.get(HelpListbox.curselection())])

HelpListbox = Listbox(Menu["Help"], width = 25)
HelpListbox.grid(row = 1, column = 1, sticky = "NEWS")
HelpListbox.bind("<<ListboxSelect>>", HelpRefresh)

HelpText = Text(Menu["Help"], wrap = WORD)
HelpText.grid(row = 1, column = 2, sticky = "NEWS")

for Nom in list(Help.keys()): HelpListbox.insert(END, Nom)


Button(Menu["Help"], text = "Menu Principal", command = lambda: ShowMenu("MainMenu"), relief = RIDGE).grid(row = 10, column = 1, columnspan = 10, sticky = "E")

####################################################################################################
####################################################################################################

def LoadProfil():
	global AllProfil
	if os.path.exists("Profil.json"):
		try:
			with open("Profil.json") as File: AllProfil = json.load(File)
		except Exception as e:
			print(e)
			messagebox.showerror("Erreur", "Le fichier des profils est illisible. Lecture d'une sauvegarde...")
			if os.path.exists("Profil.json.backup"):
				try:
					with open("Profil.json.backup") as File: AllProfil = json.load(File)
				except:
					messagebox.showerror("Erreur", "Sauvegarde illisible.")

	ProfilBox.config(values = list(AllProfil.keys())) # Actualise la liste des profil dans le menu principal

	ProfilListbox.delete(0, END)
	for ProfilData in AllProfil:
		ProfilListbox.insert(END, ProfilData)

try: SelectProfil.set(list(AllProfil.keys())[-1])
except: pass

LoadConfig()
LoadProfil()
####################################################################################################
####################################################################################################

try:
	VersionJson = json.load(urllib.request.urlopen(context = SSL_context, url = VersionDownloadLink))
	if VersionJson["LastRelease"] != LauncherVersion:
		if messagebox.askyesno("Mise à jour", "Une mise à jour est disponible (%s -> %s)" % (LauncherVersion, VersionJson["LastRelease"])):

			if os.path.exists("../MAJ.pyw"): MAJProgramName = "MAJ.pyw"
			else: MAJProgramName = "MAJ.exe"
			subprocess.Popen('cd ' + os.path.abspath("..") + ' && start ' + os.path.abspath("../%s" % MAJProgramName), shell = True)
			sys.exit()

except Exception as e: print(str(e))

####################################################################################################
####################################################################################################
Fen.after(1, RefreshNews)
mainloop()
