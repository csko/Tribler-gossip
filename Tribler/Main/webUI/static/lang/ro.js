/*
Copyright (c) 2011 BitTorrent, Inc. All rights reserved.

Use of this source code is governed by a BSD-style that can be
found in the LICENSE file.
*/

var LANG_STR = [
	  "Fișiere Torent||*.torrent||Toate Fișierele (*.*)||*.*||"
	, "OK"
	, "Anulează"
	, "Aplică"
	, "Da"
	, "Nu"
	, "Închide"
	, "Preferințe"
	, "Limba"
	, "Limbă:"
	, "Confidențialitate"
	, "Caută automat actualizări"
	, "Actualizează și la versiunile beta"
	, "Trimite informații anonime la căutarea actualizărilor"
	, "La Descărcare"
	, "Atașează .!ut la fișierele incomplete"
	, "Prealocă toate fișierele"
	, "Interzice veghea [standby] cînd sînt torente active"
	, "Opțiuni de Afișare"
	, "Confirmare la ștergerea torentelor"
	, "Confirmare a ștergerii trackerelor"
	, "Confirmare la închiderea µTorrent"
	, "Culoare de fundal alternantă"
	, "Arată viteza curentă în bara de titlu"
	, "Limitele de viteză în bara de stare"
	, "La Adăugarea Torentelor"
	, "Nu porni automat descărcarea"
	, "Activează fereastra programului"
	, "Arată o fereastră în care se văd filele existente în torent"
	, "Acțiuni prin Dublu-Clic"
	, "La donarea torentelor:"
	, "La descărcarea torentelor:"
	, "Locul Fișierelor Descărcate"
	, "Pune descărcările noi în:"
	, "Arată dialogul la adăugare manuală"
	, "Mută descărcările terminate în:"
	, "Atașează eticheta torentului"
	, "Mută doar din dosarul implicit de descărcare"
	, "Locul fișierelor torent"
	, "Stochează torentele în:"
	, "Mută torentele sarcinilor terminate în:"
	, "Încarcă automat torentele din:"
	, "Șterge torentele încărcate"
	, "Portul de Ascultare"
	, "Portul folosit pentru conexiunile intrînde:"
	, "Port Aleator"
	, "Port aleator la fiecare pornire"
	, "Activează maparea UPnP"
	, "Activează maparea NAT-PMP"
	, "Serverul Proxy"
	, "Tip:"
	, "Proxy:"
	, "Port:"
	, "Autentificare"
	, "Utilizator:"
	, "Parolă:"
	, "Rezolvă numele gazdelor prin proxy"
	, "Folosește proxy pt. conexiunile partener-la-partener [peer-to-peer]"
	, "Adaugă la excepțiile paravanului"
	, "Confidențialitate la Folosirea Serverului Proxy"
	, "Dezactivează căutarea DNS-urilor locale"
	, "Dezactivează funcțiile prin care transpiră informații de identificare"
	, "Dezactivează conexiunile nesuportate de proxy"
	, "Limitarea Globală a Vitezei de Încărcare"
	, "Vit. Max de Înc. (KB/s): [0: nelimitată]"
	, "Automată"
	, "Vit. de Încărcare cînd nu se descarcă (KB/s):"
	, "Limitarea Globală a Vitezei de Descărcare"
	, "Vit. Max de Descărcare (KB/s): [0: nelimitată]"
	, "Numărul de Conexiuni"
	, "Numărul maxim global de conexiuni:"
	, "Numărul maxim de parteneri conectați per torent:"
	, "Numărul de sloturi de încărcare per torent:"
	, "Folosește sloturi de încărcare suplimentare cînd vit. de încărcare e < 90%"
	, "Global Rate Limit Options"
	, "Aplică limitarea vitezei la gestionarea transportului [overhead]"
	, "Aplică limitarea vitezei la conexiunile uTP"
	, "Facilități BitTorrent Obișnuite"
	, "Activ. DHT (Tabelă Hașuri Distrib.)"
	, "Solicită info de răzuire [scrape]"
	, "Activează DHT pt. torentele noi"
	, "Permite schimbul de parteneri [PEX]"
	, "Descoperă partenerii locali"
	, "Limitează banda partenerilor locali"
	, "IP / NumeGazdă raportate trackerului:"
	, "Criptarea Protocolului BitTorrent"
	, "La Ieșire:"
	, "Permite conex. intrînde necriptate"
	, "Gestionează lățimea de bandă [uTP]"
	, "Activează suportul pt. trackere UDP"
	, "Activează Limita de Transfer"
	, "Setările Limitei"
	, "Tip de Limită:"
	, "Limita Lățimii de Bandă:"
	, "Perioada de Timp (zile):"
	, "Istoricul utilizării pentru perioada selectată:"
	, "Încărcat:"
	, "Descărcat:"
	, "Încărcat + Descărcat:"
	, "Perioada de Timp:"
	, "Ultimele %d zile"
	, "Reset. Istoricul"
	, "Setările Cozii de Așteptare"
	, "Numărul maxim de torente active (încărcate sau descărcate):"
	, "Numărul maxim de descărcări active:"
	, "Donează atîta timp cît"
	, "Raport de Încărcare/Descărcare Minim [Ratio] (%):"
	, "Timp minim de donare (minute):"
	, "Sarcinile de donare [seed] au o prioritate mai mare decît cele de descărcare"
	, "Cînd µTorrent atinge obiectivul de donare"
	, "Limitează viteza de încărcare la (KB/s): [0: stop]"
	, "Activează Planificatorul"
	, "Tabela Planificatorului"
	, "Setările Planificatorului"
	, "Limita vitezei de încărcare (KB/s):"
	, "Limita vitezei de descărcare (KB/s):"
	, "Dezactivează DHT la închidere"
	, "Activează Interfața Web"
	, "Autentificare"
	, "Utilizator:"
	, "Parolă:"
	, "Activează contul oaspete folosind utilizatorul:"
	, "Conectivitate"
	, "Port de ascultare alternativ (implicitul e cel de conectare):"
	, "Restricționează accesul adreselor IP (separă intrările multiple cu virgulă):"
	, "Opțiuni Avansate [ATENȚIE: Nu le modificați!]"
	, "Valoare:"
	, "Adevărată"
	, "Falsă"
	, "Setează"
	, "Popîc [popup] cu Lista Vitezelor (separă valorile multiple punînd virgulă între ele)"
	, "Ignoră popîcul [popup] cu lista vitezelor automate"
	, "Vit. de Încărcare:"
	, "Vit. de Descărcare:"
	, "Etichete Persistente [Separați etichetele multiple cu caracterul | ]"
	, "Motoare de Căutare [Format: nume| URL]"
	, "Setări de Bază ale Cașului [cache]"
	, "Cașul discului e folosit pt. a păstra în memorie datele accesate frecvent pt. a reduce nr. de citiri și scrieri pe hardisc. µTorrent administrează de obicei cașul în mod automat, dar puteți schimba acest comportament modificînd setările."
	, "Ignoră mărimea automată a cașului și specific-o manual (MB):"
	, "Diminuează folosirea memoriei cînd cașul nu e necesar"
	, "Setări Avansate ale Cașului"
	, "Activează cașarea [caching] scrierilor pe hardisc"
	, "Scrie blocurile neatinse la fiecare 2 minute"
	, "Scrie imediat părțile finalizate"
	, "Activează cașarea citirilor de pe hardisc"
	, "Dezactivează cașarea citirilor dacă viteza de încărcare e mică"
	, "Înlătură blocurile vechi din caș"
	, "Crește mărimea automată a cașului cînd e necesar"
	, "Dezactivează cașarea scrierilor pe hardisc"
	, "Dezactivează cașarea citirilor de pe hardisc"
	, "Rulează Automat Programul"
	, "Rulează acest program la terminarea torentului:"
	, "Rulează acest program cînd torentul își schimbă starea:"
	, "Poți folosi aceste comenzi:\r\n%F - Numele filei descărcate (pt. torente cu 1 filă)\r\n%D - Dosarul de salvare a filelor\r\n%N - Numele torentului\r\n%S - Starea torentului\r\n%L - Etichetă\r\n%T - Tracker\r\n%M - Șirul mesajului de stare (identic cu coloana de stare)\r\n%I - info-haș codat hexazecimal\r\n\r\nStarea e o combinație de:\r\npornit =1, verific = 2, pornire-după-verificare = 4,\r\nverificat = 8, eroare = 16, pauzat = 32, automat = 64, încărcat = 128"
	, "Proprietățile Torentului"
	, "Trackere (separați-le cu o linie goală)"
	, "Setările Lățimii de Bandă"
	, "Viteza Maximă de Încărcare (KB/s): [0: implicită]"
	, "Viteza Maximă de Descărcare (KB/s): [0: implicită]"
	, "Numărul de Sloturi de Încărcare: [0: implicit]"
	, "Donează atîta timp cît"
	, "Ignoră setările implicite"
	, "Raport Î/D minim [Ratio] (%):"
	, "Timp de donare minim (minute):"
	, "Alte Setări"
	, "Donare Inițială"
	, "Activează DHT"
	, "Sch. de Parteneri"
	, "Flux"
	, "Adresă:"
	, "Nume Familiar:"
	, "Abonare"
	, "Nu descărca automat toate itemurile"
	, "Descarcă automat toate itemurile publicate în flux"
	, "Folosește filtru inteligent pentru episoade"
	, "Fluxuri||Favorite||Istoric||"
	, "All Feeds"
	, "Setările Filtrului"
	, "Nume:"
	, "Conține:"
	, "Nu Conț.:"
	, "Salvează:"
	, "Flux:"
	, "Calitate:"
	, "Nr. Episodului: [ex. 1x12-14]"
	, "Filtrul se potrivește cu numele original, nu cu cel decodat"
	, "Nu porni automat descărcările"
	, "Filtru ager pt. ep."
	, "Oferă desc. prioritatea maximă"
	, "Intervalul Minim:"
	, "Etich. torentelor noi:"
	, "Adaugă Flux RSS..."
	, "Editează Fluxul..."
	, "Dezactivează Fluxul"
	, "Activează Fluxul"
	, "Actualizează Fluxul"
	, "Șterge Fluxul"
	, "Descarcă"
	, "Deschide Adresa în Explorator"
	, "Adaugă la Favorite"
	, "Adaugă"
	, "Șterge"
	, "TOATE"
	, "(Toate)"
	, "(potrivește mereu)||(potrivește o dată)||12 ore||1 zi||2 zile||3 zile||4 zile||1 săptămînă||2 săptămîni||3 săptămîni||1 lună||"
	, "Adaugă Flux RSS"
	, "Editează Fluxul RSS"
	, "Remove RSS Feed(s)"
	, "Really delete the %d selected RSS Feeds?"
	, "Sigur ștergi fluxul RSS \"%s\"?"
	, "Nume Întreg"
	, "Nume"
	, "Episod"
	, "Format"
	, "Codec"
	, "Date"
	, "Flux"
	, "Adresa Sursei"
	, "IP"
	, "Port"
	, "Soft"
	, "Fanioane"
	, "%"
	, "Relevanță"
	, "Descărcare"
	, "Încărcare"
	, "Solicitări"
	, "Așteptat"
	, "Încărcat"
	, "Descărcat"
	, "Erori Haș"
	, "Vit. Parteneri"
	, "MaxÎnc"
	, "MaxDesc"
	, "În Coadă"
	, "Inactiv"
	, "Realizat"
	, "Prima Parte"
	, "Nume"
	, "Nr. Părților"
	, "%"
	, "Prioritate"
	, "Mărime"
	, "salt"
	, "scăzută"
	, "normală"
	, "crescută"
	, "Descărcat:"
	, "Încărcat:"
	, "Donatori:"
	, "Rămas:"
	, "Viteza Descărcării:"
	, "Viteza Încărcării:"
	, "Parteneri:"
	, "Raport [ratio]"
	, "Salvează ca:"
	, "Haș:"
	, "Generale"
	, "Transfer"
	, "%d din %d conectați (%d în roi)"
	, "D:%s Î:%s - %s"
	, "Copiază"
	, "Resetează"
	, "Nelimitată"
	, "Rezolvă Adresele IP"
	, "Get File(s)"
	, "Nu Descărca"
	, "Prioritate Înaltă"
	, "Prioritate Scăzută"
	, "Prioritate Normală"
	, "Copiază Adresa Magnet"
	, "Șterge Datele Descărcate"
	, "Șterge Torentul"
	, "Șterge Torentul și Filele Descărcate"
	, "Forțează Reverificarea"
	, "Forțează Pornirea"
	, "Etichetă"
	, "Pauză"
	, "Proprietăți"
	, "Mută în Josul Cozii"
	, "Mută în Susul Cozii"
	, "Șterge"
	, "Șterge"
	, "Start"
	, "Stop"
	, "Active"
	, "Toate"
	, "Terminate"
	, "În Desfășurare"
	, "Inactive"
	, "Fără Etichetă"
	, "||Disponibilitate||Disponibilitate"
	, "Adăugat în"
	, "Terminat în"
	, "Progres"
	, "Descărcat"
	, "Descărcare"
	, "Estimat"
	, "Etichetă"
	, "Nume"
	, "Rang"
	, "Parteneri"
	, "Rămas"
	, "Donatori"
	, "Donatori/Parteneri"
	, "Raport"
	, "Mărime"
	, "Adresa Sursei"
	, "Stare"
	, "Încărcat"
	, "Încărcare"
	, "Sigur doriți să înlăturați cele %d torente selectate și datele descărcate?"
	, "Sigur doriți să înlăturați torentul selectat și datele descărcate?"
	, "Sigur doriți să înlăturați cele %d torente selectate?"
	, "Sigur doriți să înlăturați torentul selectat?"
	, "Sigur ștergi filtrul RSS \"%s\"?"
	, "Verificat %:.1d%%"
	, "Descarc"
	, "Eroare: %s"
	, "Terminat"
	, "Pauzat"
	, "Pus în Coadă"
	, "Donare pusă în coadă"
	, "Donez"
	, "Oprit"
	, "Introduceți Eticheta"
	, "Introduceți eticheta nouă pentru torentele selectate:"
	, "Etichetă Nouă..."
	, "Înlătură Eticheta"
	, "Generalități||Trackere||Parteneri||Părți||Fișiere||Viteză||Jurnal||"
	, "Deschide Torent"
	, "Deschide Torent din URL"
	, "Pauză"
	, "Preferințe"
	, "Mută în Josul Cozii"
	, "Mută în Susul Cozii"
	, "Șterge"
	, "Descărcător RSS"
	, "Start"
	, "Stop"
	, "Filă"
	, "Deschide Torent..."
	, "Deschide Torent din URL..."
	, "Opțiuni"
	, "Preferințe"
	, "Arată Lista de Categorii"
	, "Arată Informații Detaliate"
	, "Arată Bara de Stare"
	, "Arată Bara de Unelte"
	, "Arată Icoane pe Taburi"
	, "Ajutor"
	, "Situl µTorrent"
	, "Forumul µTorrent"
	, "Send WebUI Feedback"
	, "About µTorrent WebUI"
	, "Torente"
	, "Pauzează Toate Torentele"
	, "Repornește Toate Torentele Pauzate"
	, "D: %s%z/s"
	, " L: %z/s"
	, " G: %z/s"
	, " T: %Z"
	, "Î: %s%z/s"
	, "B"
	, "EB"
	, "GB"
	, "KB"
	, "MB"
	, "PB"
	, "TB"
	, "Avansate"
	, "Lățime de Bandă"
	, "Conexiune"
	, "Cașul Discului"
	, "Dosare"
	, "Generale"
	, "Planificator"
	, "Coada"
	, "Interfață (UI)"
	, "Interfață"
	, "BitTorrent"
	, "Web UI"
	, "Limită de Transfer"
	, "Autorulare"
	, "Arată Proprietățile||Pornește/Oprește||Deschide Dosarul||Arată Bara de Descărcare||"
	, "Dezactivată||Activată||Forțată||"
	, "(nimic)||Socks4||Socks5||HTTPS||HTTP||"
	, "Încărcări||Descărcări||Încărcări + Descărcări||"
	, "MB||GB||"
	, "1||2||5||7||10||14||15||20||21||28||30||31||"
	, "Nume"
	, "Valoare"
	, "Lun||Mar||Mie||Joi||Vin||Sîm||Dum||"
	, "Luni||Marți||Miercuri||Joi||Vineri||Sîmbătă||Duminică||"
	, "Viteză Max"
	, "Viteză Max - Folosește limitările lățimii de bandă normale globale"
	, "Limitare"
	, "Limitare - Folosește limitările lățimii de bandă specificate de planificator"
	, "Doar Donare"
	, "Doar Donare - Doar încarcă date (inclusiv incomplete)"
	, "Închidere"
	, "Închidere - Oprește toate torentele care nu sînt forțate"
	, "<= %d ore"
	, "(Ignoră)"
	, "<= %d minute"
	, "%dd %dh"
	, "%dh %dm"
	, "%dm %ds"
	, "%ds"
	, "%dw %dd"
	, "%dy %dw"
];
