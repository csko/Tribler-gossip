/*
Copyright (c) 2011 BitTorrent, Inc. All rights reserved.

Use of this source code is governed by a BSD-style that can be
found in the LICENSE file.
*/

var LANG_STR = [
	  "Torentu faili||*.torrent||Visi faili (*.*)||*.*||"
	, "Labi"
	, "Atcelt"
	, "Lietot"
	, "Jā"
	, "Nē"
	, "Aizvērt"
	, "Atribūti"
	, "Valoda"
	, "Valoda:"
	, "Privātums"
	, "Automātiski pārbaudīt atjauninājumus"
	, "Atjaunot uz Beta versijām"
	, "Pārbaudot atjauninājumus, sūtīt anonīmu informāciju"
	, "Lejupielādējot"
	, "Piešķirt .!ut nepabeigtiem failiem"
	, "Pārbaudīt failu atrašanās vietas"
	, "Nepieļaut miega režīmu, ja ir aktīvi torenti"
	, "Attēlojuma iestatījumi"
	, "Veikt apstiprināšanu dzēšot torentus"
	, "Veikt apstiprināšanu dzēšot trakerus"
	, "Izejot rādīt apstiprinājuma logu"
	, "Izmainīt saraksta fona krāsu"
	, "Rādīt tekošo ātrumu galvenajā joslā"
	, "Rādīt ātruma limitus statusa joslā"
	, "Pievienojot torentus"
	, "Neuzsākt automātisku failu vilkšanu"
	, "Aktivizēt programmas logu"
	, "Parādīt logu, kas parāda kādi faili atrodas torentā"
	, "Dubultklikšķa īpašības"
	, "Torentiem, kurus dala:"
	, "Torentiem, kurus ņem:"
	, "Novilkto failu atrašanās vieta"
	, "Ievietot velkamos failus šeit:"
	, "Pie manuālās pievienošanas rādīt logu"
	, "Pabeigtos failus pārvietot uz:"
	, "Pievienot torentu grupai"
	, "Pārvietot tikai tos, kuri atrodas noklusētajā failu mapē"
	, ".torrent failu atrašanās vieta"
	, ".torrent failu saglabāšanas vieta:"
	, "Kad pabeidz vilkt, pārvietot .torrent failu uz:"
	, "Lejuplādēt .torrent failus no:"
	, "Dzēst paņemtos .torrent failus"
	, "Savienojuma porti"
	, "Ports ienākošajiem savienojumiem:"
	, "Nejaušs ports"
	, "Mainīt portu pie katras palaišanas"
	, "Ieslēgt UPnP portu kartēšanu"
	, "Ieslēgt NAT-PMP portu kartēšanu"
	, "Proxy serveris"
	, "Tips:"
	, "Proxy:"
	, "Ports:"
	, "Autentifikācija"
	, "Lietotājs:"
	, "Parole:"
	, "Aizklāt hostu nosaukumus caur Proxy"
	, "Izmantot proxy serveri p2p savienojumiem"
	, "Pievienot Win Firewall izņēmumiem"
	, "Proxy Privacy"
	, "Disable all local DNS lookups"
	, "Disable features that leak identifying information"
	, "Disable connections unsupported by the proxy"
	, "Kopējo ātrumu ierobežojumi"
	, "Max augšupielādes ātrums (KB/s): [0: bezgalīgs]"
	, "Automātiski"
	, "Augšupielādes ātrums neko nevelkot (KB/s):"
	, "Kopējais lejupielādes limits"
	, "Max lejupielādes ātrums (KB/s): [0: bezgalīgs]"
	, "Savienojumu skaits"
	, "Maksimālais savienojumu skaits:"
	, "Maksimālais lietotāju skaits uz vienu torentu:"
	, "Augšupielādes slotu skaits uz vienu torentu:"
	, "Piešķirt papildus slotus, ja augšupielādes ātrums < 90%"
	, "Global Rate Limit Options"
	, "Lietot ātruma limitus pārsūtīšanas virstēriņam"
	, "Lietot ātruma limitus uTP savienojumiem"
	, "Papildus BitTorrent funkcijas"
	, "Ieslēgt DHT tīklu"
	, "Pieprasīt no trakera scrape inform."
	, "Ieslēgt DHT jaunajiem torentiem"
	, "Ieslēgt iesaistīto apmaiņu"
	, "Ieslēgt lokālo peeru reģistrēšanu"
	, "Ierobežot lokālo peeru tīklu"
	, "IP/PC, ziņojumu sūtīšanai trakerim:"
	, "Protokola šifrēšana"
	, "Izejošie:"
	, "Atļaut visus ienākošos savienoj."
	, "Ieslēgt tīkla pārvaldību [uTP]"
	, "Ieslēgt UDP trakeru atbalstu"
	, "Ieslēgt pārsūtījumu limitu"
	, "Limitu iestatījumi"
	, "Limit Type:"
	, "Bandwidth Cap:"
	, "Time Period (days):"
	, "Izmantojuma vēsture izvēlētajam laika posmam:"
	, "Augšupielāde:"
	, "Lejupielāde:"
	, "Augšupielāde + Lejupielāde:"
	, "Laika posms:"
	, "Pēdējās %d dienas"
	, "Nodzēst vēsturi"
	, "Rindas iestatījumi"
	, "Maksimālais aktīvo torentu skaits (pabeigto vai velkamo):"
	, "Maksimālais velkamo torentu skaits:"
	, "Dalīt līdz [noklusētās vērtības]"
	, "Minimum ratio (%):"
	, "Minimum seeding time (minutes):"
	, "Pabeigtajiem torentiem ir augstāka prioritāte par velkamajiem"
	, "Kad ir sasniegta uzstādītā attiecība"
	, "Ierobežot augšupielādi uz (KB/s): [0: apturēt]"
	, "Ieslēgt plānotāju"
	, "Plānotāja tabula"
	, "Plānotāja iestatījumi"
	, "Ierobežot augšupielādi (KB/s):"
	, "Ierobežot lejupielādi (KB/s):"
	, "Atslēgt DHT, kad izslēgts"
	, "Ieslēgt Web interfeisu"
	, "Autentificēšana"
	, "Lietotājs:"
	, "Parole:"
	, "Ieslēgt Viesu kontu ar lietotāja vārdu:"
	, "Savienojamība"
	, "Cits savienojuma ports (pēc noklusējuma, bittorrent ports):"
	, "Liegt piekļuvi sekojošām IP adresēm (vairākus ierakstus atdalīt ar komatu):"
	, "Papildus iespējas [Nav ieteicams labot!]"
	, "Vērtība:"
	, "Patiess"
	, "Nepatiess"
	, "Labi"
	, "Ātruma attēlošanas grafiks [Vērtības atdala ar komatu]"
	, "Izmainīt esošo ātruma grafiku"
	, "Augšupielādes ātrums:"
	, "Lejupielādes ātrums:"
	, "Patstāvīgās grupas [Vairākas grupas atdala ar | simbolu]"
	, "Meklēšanas avoti [Formāts: nosaukums|adrese]"
	, "Galvenie krātuves iestatījumi"
	, "Krātuve saglabā un apstrādā regulāri izmantotos datus, tādējādi tiek mazāk noslogots cietais disks. Parasti µTorrent pats nosaka nepieciešamo krātuves izmēru (32MB), taču ja jūs vēlaties, tad variet manuāli izmainīt šos iestatījumus."
	, "Dzēst automātisko krātuves izmēru un izvēlēties savu (MB):"
	, "Atbrīvot atmiņu, kad tā nav vajadzīga krātuvei"
	, "Papildus krātuves iestatījumi"
	, "Saglabāt krātuvē datus, kas tiek ierakstīti diskā"
	, "Ik pēc 2 minūtēm izņemt neizmantotās daļiņas"
	, "Automātiski izņemt pabeigtās daļiņas"
	, "Saglabāt no diska veiktos nolasījumus"
	, "Izslēgt diska nolasījumu saglabāšanu pie zema lejupielādes ātruma"
	, "Izņemt no krātuves neizmantotās daļiņas"
	, "Palielināt krātuves izmēru, kad tā tiek pārkārtota"
	, "Atslēgt Windows caching, kad disks raksta"
	, "Atslēgt Windows caching, kad disks lasa"
	, "Run Program"
	, "Run this program when a torrent finishes:"
	, "Run this program when a torrent changes state:"
	, "You can use these commands:\r\n%F - Name of downloaded file (for single file torrents)\r\n%D - Directory where files are saved\r\n%N - Title of torrent\r\n%S - State of torrent\r\n%L - Label\r\n%T - Tracker\r\n%M - Status message string (same as status column)\r\n%I - hex encoded info-hash\r\n\r\nState is a combination of:\r\nstarted = 1, checking = 2, start-after-check = 4,\r\nchecked = 8, error = 16, paused = 32, auto = 64, loaded = 128"
	, "Torenta rekvizīti"
	, "Trakeri (atdalīt ar tukšu rindu)"
	, "Līnijas iestatījumi"
	, "Max augšupielādes ātrums (KB/s): [0: neierobežots]"
	, "Max lejupielādes ātrums (KB/s): [0: neierobežots]"
	, "Augšupielādes slotu skaits: [0: pēc noklusējuma]"
	, "Dalīt līdz"
	, "Ignorēt noklusētos iestatījumus"
	, "Minimum ratio (%):"
	, "Minimum seeding time (minutes):"
	, "Citi iestatījumi"
	, "Ātrā dalīšana"
	, "Ieslēgt DHT"
	, "Iesaistīto apmaiņa"
	, "Kanāls"
	, "Kanāla adrese:"
	, "Nosaukums:"
	, "Papildus"
	, "Neuzsākt automātisku failu lejupielādi"
	, "Automātiski lejupielādēt failus, kas parādās kanālā"
	, "Izmantot gudro epizožu filtru"
	, "Kanāli||Izlase||Vēsture||"
	, "All Feeds"
	, "Filtra uzstādījumi"
	, "Nosaukums:"
	, "Filtrēt:"
	, "Izņemot:"
	, "Saglabāt:"
	, "Kanāls:"
	, "Kvalitāte:"
	, "Epizodes Nr.: [piem. 1x12-14]"
	, "Filtrs sakrīt ar oriģinālo nosaukumu"
	, "Neuzsākt automātisku lejupielādi"
	, "Gudrais ep. filtrs"
	, "Lejupielādei piešķirt augstāko prior."
	, "Minimālais intervāls:"
	, "Grupa jaunajiem torentiem"
	, "Pievienot RSS kanālu..."
	, "Labot kanālu..."
	, "Izslēgt kanālu"
	, "Ieslēgt kanālu"
	, "Atjaunot kanālu"
	, "Dzēst kanālu"
	, "Lejupielādēt"
	, "Atvērt adresi pārlūkā"
	, "Pievienot izlasei"
	, "Pievienot"
	, "Dzēst"
	, "Visi"
	, "(Visi)"
	, "(vienmēr sakrist)||(sakrist vienreiz)||12 stundas||1 diena||2 dienas||3 dienas||1 nedēļa||2 nedēļas||3 nedēļas||1 mēnesis||"
	, "Pievienot RSS kanālu"
	, "Labot RSS kanālu"
	, "Remove RSS Feed(s)"
	, "Really delete the %d selected RSS Feeds?"
	, "Vai tiešām vēlaties dzēst RSS kanālu \"%s\"?"
	, "Pilns nosaukums"
	, "Nosaukums"
	, "Epizode"
	, "Formāts"
	, "Kodeks"
	, "Date"
	, "Kanāls"
	, "Adrese"
	, "IP"
	, "Ports"
	, "Klients"
	, "Karogi"
	, "%"
	, "Svarīgums"
	, "Lejupiel. ātrums"
	, "Augšupiel. ātrums"
	, "Pieprasījumi"
	, "Gaidīts"
	, "Augšupielādēts"
	, "Lejupielādēts"
	, "Hasherr"
	, "Iesaistīto att."
	, "Maks. augšupiel."
	, "Maks. lejupiel."
	, "Ierindots"
	, "Neaktīvs"
	, "Pabeigts"
	, "Pirmā daļiņa"
	, "Nosaukums"
	, "Daļiņu skaits"
	, "%"
	, "Prioritāte"
	, "Izmērs"
	, "izlaist"
	, "zema"
	, "normāla"
	, "augsta"
	, "Novilkts:"
	, "Izdalīts:"
	, "Devēji:"
	, "Atlicis:"
	, "Lejupiel. ātrums:"
	, "Augšup. ātrums:"
	, "Iesaistītie:"
	, "A/L attiecība:"
	, "Saglabāt kā:"
	, "Hash:"
	, "Vispārīgi"
	, "Pārsūtīti"
	, "%d no %d ir savienoti (%d gaida)"
	, "L:%s A:%s - %s"
	, "Kopēt"
	, "Nodzēst"
	, "Neierobežots"
	, "Aizklāt IP"
	, "Get File(s)"
	, "Nevilkt"
	, "Augsta prioritāte"
	, "Zema prioritāte"
	, "Normāla prioritāte"
	, "Kopēt Magnet-URI"
	, "Dzēst datus"
	, "Dzēst .torrent failu"
	, "Dzēst .torrent un datus"
	, "Piespiedu pārbaude"
	, "Piespiedu sākšana"
	, "Grupa"
	, "Pauze"
	, "Rekvizīti"
	, "Pārvietot lejup"
	, "Pārvietot augšup"
	, "Izmest"
	, "Izmest un"
	, "Sākt"
	, "Apturēt"
	, "Aktīvi"
	, "Visi"
	, "Pabeigti"
	, "Lejupielādē"
	, "Neaktīvi"
	, "Bez grupas"
	, "||Pieej.||Pieejamība"
	, "Pievienots"
	, "Pabeigts"
	, "Izpildīti"
	, "Izdalīti"
	, "Lejupiel. ātrums"
	, "Atl. laiks"
	, "Grupa"
	, "Nosaukums"
	, "#"
	, "Iesaistītie"
	, "Atlicis"
	, "Devēji"
	, "Devēji/Iesaistītie"
	, "Attiecība"
	, "Izmērs"
	, "Adrese"
	, "Statuss"
	, "Atdots"
	, "Augšupiel. ātrums"
	, "Vai tiešām vēlaties dzēst atzīmētos torentus un visus ar tiem saistītos datus?"
	, "Vai tiešām vēlaties dzēst atzīmēto torentu un visus ar to saistītos datus?"
	, "Vai tiešām vēlaties dzēst %d atzīmētos torentus?"
	, "Vai tiešām vēlaties dzēst atzīmēto torentu?"
	, "Vai tiešām vēlaties dzēst RSS filtru \"%s\"?"
	, "Pārbaudīti %:.1d%%"
	, "Ņem"
	, "Kļūda: %s"
	, "Pabeigts"
	, "Nopauzēts"
	, "Sakārtots"
	, "Gaida rindā"
	, "Dod"
	, "Apturēts"
	, "Izveidot grupu"
	, "Ievadiet grupas nosaukumu izvēlētajiem torentiem:"
	, "Jauna grupa..."
	, "Izdzēst grupu"
	, "Galvenā||Trakeri||Iesaistītie||Daļiņas||Faili||Ātrums||Žurnāls||"
	, "Pievienot torentu"
	, "Pievienot torentu pēc adreses"
	, "Pauze"
	, "Atribūti"
	, "Pārvietot lejup"
	, "Pārvietot augšup"
	, "Izmest"
	, "RSS lejuplādētājs"
	, "Sākt"
	, "Apturēt"
	, "Fails"
	, "Pievienot torentu..."
	, "Pievienot torentu pēc adreses..."
	, "Iestatījumi"
	, "Konfigurācija"
	, "Rādīt kategoriju sarakstu"
	, "Rādīt detalizētu informāciju"
	, "Rādīt statusa joslu"
	, "Rādīt rīkjoslu"
	, "Rīkjoslas ikonas"
	, "Palīdzība"
	, "µTorrent mājas lapa"
	, "µTorrent forums"
	, "Send WebUI Feedback"
	, "About µTorrent WebUI"
	, "Torenti"
	, "Nopauzēt visus torentus"
	, "Palaist visus torentus"
	, "D: %s%z/s"
	, " L: %z/s"
	, " O: %z/s"
	, " T: %Z"
	, "U: %s%z/s"
	, "B"
	, "EB"
	, "GB"
	, "KB"
	, "MB"
	, "PB"
	, "TB"
	, "Papildus"
	, "Joslas platums"
	, "Savienojumi"
	, "Diska krātuve"
	, "Mapes"
	, "Galvenā"
	, "Plānotājs"
	, "Rinda"
	, "UI ekstras"
	, "UI iestatījumi"
	, "BitTorrent"
	, "Web UI"
	, "Pārsūtījumu limits"
	, "Run Program"
	, "Rādīt rekvizītus||Sākt/Apturēt||Atvērt mapi||Rādīt lejupielādes lodziņu||"
	, "Izslēgts||Ieslēgts||Piespiedu||"
	, "(tukšs)||Socks4||Socks5||HTTPS||HTTP||"
	, "Augšupielāde||Lejupielāde||Augšupielāde + Lejupielāde||"
	, "MB||GB||"
	, "1||2||5||7||10||14||15||20||21||28||30||31||"
	, "Nosaukums"
	, "Vienība"
	, "Pir||Otr||Tre||Cet||Pie||Ses||Svē||"
	, "Pirmdiena||Otrdiena||Trešdiena||Ceturtdiena||Piektdiena||Sestdiena||Svētdiena||"
	, "Max ātrums"
	, "Max ātrums - Izmanto maksimālos  tīkla ātruma limitus"
	, "Limitēts"
	, "Limitēts - Izmanto plānotāja norādītos tīkla ātruma limitus"
	, "Tikai dod"
	, "Tikai dod - Tikai augšupielādē failus (ieskaitot nepabeigtos)"
	, "Izslēgts"
	, "Izslēgts - Aptur visus torentus"
	, "<= %d stundas"
	, "(Ignorēt)"
	, "<= %d minūtes"
	, "%dd %dh"
	, "%dh %dm"
	, "%dm %ds"
	, "%ds"
	, "%dw %dd"
	, "%dy %dw"
];
