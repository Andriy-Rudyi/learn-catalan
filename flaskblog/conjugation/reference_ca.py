"""Reference conjugations used to verify what we serve.

Every form here is standard (IEC) Catalan, written from grammar
references rather than from verbecc's output, so it can be used as an
oracle: :mod:`flaskblog.conjugation.audit` and the tests compare the
conjugator against this table and fail on any difference.

A form may list acceptable variants separated by ``|`` - either because
both spellings are standard (``duu|du``) or because the 2016 IEC reform
dropped a diacritic that older sources still carry (``sóc|soc``).

Keys are ``mood.tense`` as verbecc names them.  Values hold the six
grammatical persons in order, without pronouns; ``particip`` and
``gerundi`` hold a single form.  A tense may be omitted - what is listed
is checked, what is missing is not claimed.
"""

PRESENT = "indicatiu.present"
IMPERFET = "indicatiu.imperfet"
FUTUR = "indicatiu.futur"
SUBJ_PRESENT = "subjuntiu.present"
PARTICIP = "particip"
GERUNDI = "gerundi"

# Verbs whose conjugation the site claims to have verified.
REFERENCE = {
    # --- the auxiliaries and the most frequent irregulars ----------------
    "ser": {
        PRESENT: ["sóc|soc", "ets", "és", "som", "sou", "són|son"],
        IMPERFET: ["era", "eres", "era", "érem", "éreu", "eren"],
        FUTUR: ["seré", "seràs", "serà", "serem", "sereu", "seran"],
        SUBJ_PRESENT: ["sigui", "siguis", "sigui", "siguem", "sigueu", "siguin"],
        PARTICIP: "estat|sigut",
        GERUNDI: "sent|essent",
    },
    "ésser": {
        PRESENT: ["sóc|soc", "ets", "és", "som", "sou", "són|son"],
        PARTICIP: "estat|sigut",
    },
    "estar": {
        PRESENT: ["estic", "estàs", "està", "estem", "esteu", "estan"],
        IMPERFET: ["estava", "estaves", "estava", "estàvem", "estàveu", "estaven"],
        FUTUR: ["estaré", "estaràs", "estarà", "estarem", "estareu", "estaran"],
        SUBJ_PRESENT: ["estigui", "estiguis", "estigui", "estiguem", "estigueu", "estiguin"],
        PARTICIP: "estat",
        GERUNDI: "estant",
    },
    "haver": {
        PRESENT: ["he", "has", "ha", "hem|havem", "heu|haveu", "han"],
        FUTUR: ["hauré", "hauràs", "haurà", "haurem", "haureu", "hauran"],
        SUBJ_PRESENT: ["hagi", "hagis", "hagi", "hàgim|haguem", "hàgiu|hagueu", "hagin"],
        PARTICIP: "hagut",
        GERUNDI: "havent",
    },
    "tenir": {
        PRESENT: ["tinc", "tens", "té", "tenim", "teniu", "tenen"],
        FUTUR: ["tindré", "tindràs", "tindrà", "tindrem", "tindreu", "tindran"],
        SUBJ_PRESENT: ["tingui", "tinguis", "tingui", "tinguem", "tingueu", "tinguin"],
        PARTICIP: "tingut",
        GERUNDI: "tenint",
    },
    "tindre": {
        PRESENT: ["tinc", "tens", "té", "tenim", "teniu", "tenen"],
        PARTICIP: "tingut",
    },
    "fer": {
        PRESENT: ["faig", "fas", "fa", "fem", "feu", "fan"],
        IMPERFET: ["feia", "feies", "feia", "fèiem", "fèieu", "feien"],
        FUTUR: ["faré", "faràs", "farà", "farem", "fareu", "faran"],
        SUBJ_PRESENT: ["faci", "facis", "faci", "fem|facem", "feu|faceu", "facin"],
        PARTICIP: "fet",
        GERUNDI: "fent",
    },
    "desfer": {
        PRESENT: ["desfaig", "desfàs", "desfà", "desfem", "desfeu", "desfan"],
        PARTICIP: "desfet",
        GERUNDI: "desfent",
    },
    "refer": {
        PRESENT: ["refaig", "refàs", "refà", "refem", "refeu", "refan"],
        PARTICIP: "refet",
    },
    "anar": {
        PRESENT: ["vaig", "vas", "va", "anem", "aneu", "van"],
        IMPERFET: ["anava", "anaves", "anava", "anàvem", "anàveu", "anaven"],
        FUTUR: ["aniré", "aniràs", "anirà", "anirem", "anireu", "aniran"],
        SUBJ_PRESENT: ["vagi", "vagis", "vagi", "anem", "aneu", "vagin"],
        PARTICIP: "anat",
        GERUNDI: "anant",
    },
    "dir": {
        PRESENT: ["dic", "dius", "diu", "diem", "dieu", "diuen"],
        IMPERFET: ["deia", "deies", "deia", "dèiem", "dèieu", "deien"],
        FUTUR: ["diré", "diràs", "dirà", "direm", "direu", "diran"],
        SUBJ_PRESENT: ["digui", "diguis", "digui", "diguem", "digueu", "diguin"],
        PARTICIP: "dit",
        GERUNDI: "dient",
    },
    "poder": {
        PRESENT: ["puc", "pots", "pot", "podem", "podeu", "poden"],
        FUTUR: ["podré", "podràs", "podrà", "podrem", "podreu", "podran"],
        SUBJ_PRESENT: ["pugui", "puguis", "pugui", "puguem", "pugueu", "puguin"],
        PARTICIP: "pogut",
        GERUNDI: "podent",
    },
    "voler": {
        PRESENT: ["vull", "vols", "vol", "volem", "voleu", "volen"],
        IMPERFET: ["volia", "volies", "volia", "volíem", "volíeu", "volien"],
        FUTUR: ["voldré", "voldràs", "voldrà", "voldrem", "voldreu", "voldran"],
        SUBJ_PRESENT: ["vulgui", "vulguis", "vulgui", "vulguem", "vulgueu", "vulguin"],
        PARTICIP: "volgut",
        GERUNDI: "volent",
    },
    "saber": {
        PRESENT: ["sé", "saps", "sap", "sabem", "sabeu", "saben"],
        IMPERFET: ["sabia", "sabies", "sabia", "sabíem", "sabíeu", "sabien"],
        FUTUR: ["sabré", "sabràs", "sabrà", "sabrem", "sabreu", "sabran"],
        SUBJ_PRESENT: ["sàpiga", "sàpigues", "sàpiga", "sapiguem", "sapigueu", "sàpiguen"],
        PARTICIP: "sabut",
        GERUNDI: "sabent",
    },
    "veure": {
        PRESENT: ["veig", "veus", "veu", "veiem", "veieu", "veuen"],
        IMPERFET: ["veia", "veies", "veia", "vèiem", "vèieu", "veien"],
        FUTUR: ["veuré", "veuràs", "veurà", "veurem", "veureu", "veuran"],
        SUBJ_PRESENT: ["vegi", "vegis", "vegi", "vegem|veiem", "vegeu|veieu", "vegin"],
        PARTICIP: "vist",
        GERUNDI: "veient",
    },
    "venir": {
        PRESENT: ["vinc", "vens|véns", "ve|vé", "venim", "veniu", "venen|vénen"],
        FUTUR: ["vindré", "vindràs", "vindrà", "vindrem", "vindreu", "vindran"],
        SUBJ_PRESENT: ["vingui", "vinguis", "vingui", "vinguem", "vingueu", "vinguin"],
        PARTICIP: "vingut",
        GERUNDI: "venint",
    },
    "viure": {
        PRESENT: ["visc", "vius", "viu", "vivim", "viviu", "viuen"],
        IMPERFET: ["vivia", "vivies", "vivia", "vivíem", "vivíeu", "vivien"],
        FUTUR: ["viuré", "viuràs", "viurà", "viurem", "viureu", "viuran"],
        SUBJ_PRESENT: ["visqui", "visquis", "visqui", "visquem", "visqueu", "visquin"],
        PARTICIP: "viscut",
        GERUNDI: "vivint",
    },
    "conviure": {
        PRESENT: ["convisc", "convius", "conviu", "convivim", "conviviu", "conviuen"],
        PARTICIP: "conviscut",
        GERUNDI: "convivint",
    },
    "escriure": {
        PRESENT: ["escric", "escrius", "escriu", "escrivim", "escriviu", "escriuen"],
        FUTUR: ["escriuré", "escriuràs", "escriurà", "escriurem", "escriureu", "escriuran"],
        SUBJ_PRESENT: ["escrigui", "escriguis", "escrigui", "escriguem", "escrigueu", "escriguin"],
        PARTICIP: "escrit",
        GERUNDI: "escrivint",
    },
    "beure": {
        PRESENT: ["bec", "beus", "beu", "bevem", "beveu", "beuen"],
        PARTICIP: "begut",
        GERUNDI: "bevent",
    },
    "deure": {
        PRESENT: ["dec", "deus", "deu", "devem", "deveu", "deuen"],
        PARTICIP: "degut",
        GERUNDI: "devent",
    },
    "moure": {
        PRESENT: ["moc", "mous", "mou", "movem", "moveu", "mouen"],
        PARTICIP: "mogut",
        GERUNDI: "movent",
    },
    "creure": {
        PRESENT: ["crec", "creus", "creu", "creiem", "creieu", "creuen"],
        PARTICIP: "cregut",
        GERUNDI: "creient",
    },
    "seure": {
        PRESENT: ["sec", "seus", "seu", "seiem", "seieu", "seuen"],
        PARTICIP: "segut",
        GERUNDI: "seient",
    },
    "caure": {
        PRESENT: ["caic", "caus", "cau", "caiem", "caieu", "cauen"],
        PARTICIP: "caigut",
        GERUNDI: "caient",
    },
    "treure": {
        PRESENT: ["trec", "treus", "treu", "traiem", "traieu", "treuen"],
        SUBJ_PRESENT: ["tregui", "treguis", "tregui", "traguem", "tragueu", "treguin"],
        PARTICIP: "tret",
        GERUNDI: "traient",
    },
    "traure": {
        PRESENT: ["trec", "treus", "treu", "traiem", "traieu", "treuen"],
        PARTICIP: "tret",
        GERUNDI: "traent",
    },
    "riure": {
        PRESENT: ["ric", "rius", "riu", "riem", "rieu", "riuen"],
        PARTICIP: "rigut",
        GERUNDI: "rient",
    },
    "dur": {
        PRESENT: ["duc", "duus|dus", "duu|du", "duem", "dueu", "duen"],
        PARTICIP: "dut",
        GERUNDI: "duent",
    },
    "prendre": {
        PRESENT: ["prenc", "prens", "pren", "prenem", "preneu", "prenen"],
        FUTUR: ["prendré", "prendràs", "prendrà", "prendrem", "prendreu", "prendran"],
        SUBJ_PRESENT: ["prengui", "prenguis", "prengui", "prenguem", "prengueu", "prenguin"],
        PARTICIP: "pres",
        GERUNDI: "prenent",
    },
    "aprendre": {
        PRESENT: ["aprenc", "aprens", "aprèn", "aprenem", "apreneu", "aprenen"],
        FUTUR: ["aprendré", "aprendràs", "aprendrà", "aprendrem", "aprendreu", "aprendran"],
        SUBJ_PRESENT: ["aprengui", "aprenguis", "aprengui", "aprenguem", "aprengueu", "aprenguin"],
        PARTICIP: "après",
        GERUNDI: "aprenent",
    },
    "comprendre": {
        PRESENT: ["comprenc", "comprens", "comprèn", "comprenem", "compreneu", "comprenen"],
        PARTICIP: "comprès",
        GERUNDI: "comprenent",
    },
    "entendre": {
        PRESENT: ["entenc", "entens", "entén", "entenem", "enteneu", "entenen"],
        FUTUR: ["entendré", "entendràs", "entendrà", "entendrem", "entendreu", "entendran"],
        PARTICIP: "entès",
        GERUNDI: "entenent",
    },
    "atendre": {
        PRESENT: ["atenc", "atens", "atén", "atenem", "ateneu", "atenen"],
        PARTICIP: "atès",
        GERUNDI: "atenent",
    },
    "perdre": {
        PRESENT: ["perdo", "perds", "perd", "perdem", "perdeu", "perden"],
        FUTUR: ["perdré", "perdràs", "perdrà", "perdrem", "perdreu", "perdran"],
        SUBJ_PRESENT: ["perdi", "perdis", "perdi", "perdem", "perdeu", "perdin"],
        PARTICIP: "perdut",
        GERUNDI: "perdent",
    },
    "vendre": {
        PRESENT: ["venc", "vens", "ven", "venem", "veneu", "venen"],
        FUTUR: ["vendré", "vendràs", "vendrà", "vendrem", "vendreu", "vendran"],
        PARTICIP: "venut",
        GERUNDI: "venent",
    },
    "respondre": {
        PRESENT: ["responc", "respons", "respon", "responem", "responeu", "responen"],
        PARTICIP: "respost",
        GERUNDI: "responent",
    },
    "compondre": {
        PRESENT: ["componc", "compons", "compon", "componem", "componeu", "componen"],
        PARTICIP: "compost",
    },
    "confondre": {
        PRESENT: ["confonc", "confons", "confon", "confonem", "confoneu", "confonen"],
        FUTUR: ["confondré", "confondràs", "confondrà", "confondrem", "confondreu", "confondran"],
        PARTICIP: "confós",
    },
    "fondre": {
        PRESENT: ["fonc", "fons", "fon", "fonem", "foneu", "fonen"],
        PARTICIP: "fos",
    },
    "resoldre": {
        PRESENT: ["resolc", "resols", "resol", "resolem", "resoleu", "resolen"],
        PARTICIP: "resolt",
    },
    "conèixer": {
        PRESENT: ["conec", "coneixes", "coneix", "coneixem", "coneixeu", "coneixen"],
        FUTUR: ["coneixeré", "coneixeràs", "coneixerà", "coneixerem", "coneixereu", "coneixeran"],
        PARTICIP: "conegut",
        GERUNDI: "coneixent",
    },
    "aparèixer": {
        PRESENT: ["aparec", "apareixes", "apareix", "apareixem", "apareixeu", "apareixen"],
        PARTICIP: "aparegut",
    },
    "merèixer": {
        PRESENT: ["mereixo", "mereixes", "mereix", "mereixem", "mereixeu", "mereixen"],
        PARTICIP: "merescut",
    },
    "créixer": {
        PRESENT: ["creixo", "creixes", "creix", "creixem", "creixeu", "creixen"],
        FUTUR: ["creixeré", "creixeràs", "creixerà", "creixerem", "creixereu", "creixeran"],
        PARTICIP: "crescut",
        GERUNDI: "creixent",
    },
    "néixer": {
        PRESENT: ["neixo", "neixes", "neix", "naixem", "naixeu", "neixen"],
        PARTICIP: "nascut",
        GERUNDI: "naixent",
    },
    "nàixer": {
        PRESENT: ["naixo", "naixes", "naix", "naixem", "naixeu", "naixen"],
        FUTUR: ["naixeré", "naixeràs", "naixerà", "naixerem", "naixereu", "naixeran"],
        PARTICIP: "nascut",
        GERUNDI: "naixent",
    },
    "témer": {
        PRESENT: ["temo", "tems", "tem", "temem", "temeu", "temen"],
        FUTUR: ["temeré", "temeràs", "temerà", "temerem", "temereu", "temeran"],
        PARTICIP: "temut",
        GERUNDI: "tement",
    },
    "córrer": {
        PRESENT: ["corro", "corres", "corre", "correm", "correu", "corren"],
        FUTUR: ["correré", "correràs", "correrà", "correrem", "correreu", "correran"],
        PARTICIP: "corregut",
        GERUNDI: "corrent",
    },
    "pertànyer": {
        PRESENT: ["pertanyo", "pertanys", "pertany", "pertanyem", "pertanyeu", "pertanyen"],
        FUTUR: ["pertanyeré", "pertanyeràs", "pertanyerà", "pertanyerem", "pertanyereu", "pertanyeran"],
        PARTICIP: "pertangut",
        GERUNDI: "pertanyent",
    },
    "vèncer": {
        PRESENT: ["venço", "vences", "venç", "vencem", "venceu", "vencen"],
        PARTICIP: "vençut",
        GERUNDI: "vencent",
    },
    "tòrcer": {
        PRESENT: ["torço", "torces", "torç", "torcem", "torceu", "torcen"],
        PARTICIP: "torçut",
        GERUNDI: "torcent",
    },
    "valer": {
        PRESENT: ["valc", "vals", "val", "valem", "valeu", "valen"],
        FUTUR: ["valdré", "valdràs", "valdrà", "valdrem", "valdreu", "valdran"],
        PARTICIP: "valgut",
        GERUNDI: "valent",
    },
    "soler": {
        PRESENT: ["solc", "sols", "sol", "solem", "soleu", "solen"],
        PARTICIP: "solgut",
    },
    "rebre": {
        PRESENT: ["rebo", "reps", "rep", "rebem", "rebeu", "reben"],
        FUTUR: ["rebré", "rebràs", "rebrà", "rebrem", "rebreu", "rebran"],
        PARTICIP: "rebut",
        GERUNDI: "rebent",
    },
    "cabre": {
        PRESENT: ["cabo", "caps", "cap", "cabem", "cabeu", "caben"],
        PARTICIP: "cabut",
    },
    "caldre": {
        PRESENT: ["-", "-", "cal", "-", "-", "calen"],
        SUBJ_PRESENT: ["-", "-", "calgui", "-", "-", "calguin"],
        PARTICIP: "calgut",
        GERUNDI: "calent",
    },
    "cloure": {
        PRESENT: ["cloc", "clous", "clou", "cloem", "cloeu", "clouen"],
        PARTICIP: "clos",
    },
    "complaure": {
        PRESENT: ["complac", "complaus", "complau", "complaem", "complaeu", "complauen"],
        PARTICIP: "complagut",
    },
    "jaure": {
        PRESENT: ["jec", "jeus", "jeu", "jaiem", "jaieu", "jeuen"],
        PARTICIP: "jagut",
        GERUNDI: "jaient",
    },
    "cerndre": {
        PRESENT: ["cerno", "cerns", "cern", "cernem", "cerneu", "cernen"],
        FUTUR: ["cerndré", "cerndràs", "cerndrà", "cerndrem", "cerndreu", "cerndran"],
        PARTICIP: "cernut",
    },
    "expendre": {
        PRESENT: ["expenc", "expens", "expèn", "expenem", "expeneu", "expenen"],
        PARTICIP: "expès",
    },
    # --- regular and semi-regular patterns, one verb per template --------
    "cantar": {
        PRESENT: ["canto", "cantes", "canta", "cantem", "canteu", "canten"],
        IMPERFET: ["cantava", "cantaves", "cantava", "cantàvem", "cantàveu", "cantaven"],
        FUTUR: ["cantaré", "cantaràs", "cantarà", "cantarem", "cantareu", "cantaran"],
        SUBJ_PRESENT: ["canti", "cantis", "canti", "cantem", "canteu", "cantin"],
        PARTICIP: "cantat",
        GERUNDI: "cantant",
    },
    "parlar": {
        PRESENT: ["parlo", "parles", "parla", "parlem", "parleu", "parlen"],
        PARTICIP: "parlat",
        GERUNDI: "parlant",
    },
    "menjar": {
        PRESENT: ["menjo", "menges", "menja", "mengem", "mengeu", "mengen"],
        PARTICIP: "menjat",
        GERUNDI: "menjant",
    },
    "començar": {
        PRESENT: ["començo", "comences", "comença", "comencem", "comenceu", "comencen"],
        SUBJ_PRESENT: ["comenci", "comencis", "comenci", "comencem", "comenceu", "comencin"],
        PARTICIP: "començat",
    },
    "trencar": {
        PRESENT: ["trenco", "trenques", "trenca", "trenquem", "trenqueu", "trenquen"],
        SUBJ_PRESENT: ["trenqui", "trenquis", "trenqui", "trenquem", "trenqueu", "trenquin"],
        PARTICIP: "trencat",
    },
    "pagar": {
        PRESENT: ["pago", "pagues", "paga", "paguem", "pagueu", "paguen"],
        SUBJ_PRESENT: ["pagui", "paguis", "pagui", "paguem", "pagueu", "paguin"],
        PARTICIP: "pagat",
    },
    "jugar": {
        PRESENT: ["jugo", "jugues", "juga", "juguem", "jugueu", "juguen"],
        PARTICIP: "jugat",
    },
    "estudiar": {
        PRESENT: ["estudio", "estudies", "estudia", "estudiem", "estudieu", "estudien"],
        SUBJ_PRESENT: ["estudiï", "estudiïs", "estudiï", "estudiem", "estudieu", "estudiïn"],
        PARTICIP: "estudiat",
    },
    "evacuar": {
        PRESENT: ["evacuo", "evacues", "evacua", "evacuem", "evacueu", "evacuen"],
        PARTICIP: "evacuat",
    },
    "dormir": {
        PRESENT: ["dormo", "dorms", "dorm", "dormim", "dormiu", "dormen"],
        PARTICIP: "dormit",
        GERUNDI: "dormint",
    },
    "obrir": {
        PRESENT: ["obro", "obres", "obre", "obrim", "obriu", "obren"],
        PARTICIP: "obert",
        GERUNDI: "obrint",
    },
    "omplir": {
        PRESENT: ["omplo", "omples", "omple", "omplim", "ompliu", "omplen"],
        PARTICIP: "omplert",
    },
    "servir": {
        PRESENT: ["serveixo", "serveixes", "serveix", "servim", "serviu", "serveixen"],
        PARTICIP: "servit",
        GERUNDI: "servint",
    },
    "llegir": {
        PRESENT: ["llegeixo", "llegeixes", "llegeix", "llegim", "llegiu", "llegeixen"],
        PARTICIP: "llegit",
        GERUNDI: "llegint",
    },
    "obeir": {
        PRESENT: ["obeeixo", "obeeixes", "obeeix", "obeïm", "obeïu", "obeeixen"],
        PARTICIP: "obeït",
        GERUNDI: "obeint",
    },
    "imprimir": {
        PRESENT: ["imprimeixo", "imprimeixes", "imprimeix", "imprimim", "imprimiu", "imprimeixen"],
        PARTICIP: "imprès",
    },
    "complir": {
        PRESENT: ["compleixo", "compleixes", "compleix", "complim", "compliu", "compleixen"],
        PARTICIP: "complert|complit",
    },
    "oferir": {
        PRESENT: ["ofereixo", "ofereixes", "ofereix", "oferim", "oferiu", "ofereixen"],
        PARTICIP: "ofert",
    },
    "sortir": {
        PRESENT: ["surto", "surts", "surt", "sortim", "sortiu", "surten"],
        PARTICIP: "sortit",
    },
    "collir": {
        PRESENT: ["cullo", "culls", "cull", "collim", "colliu", "cullen"],
        PARTICIP: "collit",
    },
    "escollir": {
        PRESENT: ["escullo", "esculls", "escull", "escollim", "escolliu", "escullen"],
        PARTICIP: "escollit",
    },
    "fugir": {
        PRESENT: ["fujo", "fuges", "fuig", "fugim", "fugiu", "fugen"],
        PARTICIP: "fugit",
    },
    "cosir": {
        PRESENT: ["cuso", "cuses", "cus", "cosim", "cosiu", "cusen"],
        PARTICIP: "cosit",
    },
    "tossir": {
        PRESENT: ["tusso", "tusses", "tus", "tossim", "tossiu", "tussen"],
        PARTICIP: "tossit",
    },
    "mentir": {
        PRESENT: ["menteixo", "menteixes", "menteix", "mentim", "mentiu", "menteixen"],
        PARTICIP: "mentit",
    },
    "sentir": {
        PRESENT: ["sento", "sents", "sent", "sentim", "sentiu", "senten"],
        PARTICIP: "sentit",
    },
    "eixir": {
        PRESENT: ["ixo", "ixes", "ix", "eixim", "eixiu", "ixen"],
        PARTICIP: "eixit",
    },
    "prevenir": {
        PRESENT: ["previnc", "prevens|prevéns", "prevé", "prevenim", "preveniu", "prevenen|prevénen"],
        PARTICIP: "previngut",
    },
    "mantenir": {
        PRESENT: ["mantinc", "mantens", "manté", "mantenim", "manteniu", "mantenen"],
        PARTICIP: "mantingut",
    },
    "contradir": {
        PRESENT: ["contradic", "contradius", "contradiu", "contradiem", "contradieu", "contradiuen"],
        PARTICIP: "contradit",
    },
    "doldre": {
        PRESENT: ["dolc", "dols", "dol", "dolem", "doleu", "dolen"],
        PARTICIP: "dolgut",
    },
    # --- families repaired by the corrections file -----------------------
    "admetre": {
        PRESENT: ["admeto", "admets", "admet", "admetem", "admeteu", "admeten"],
        FUTUR: ["admetré", "admetràs", "admetrà", "admetrem", "admetreu", "admetran"],
        PARTICIP: "admès",
    },
    "prometre": {
        PRESENT: ["prometo", "promets", "promet", "prometem", "prometeu", "prometen"],
        PARTICIP: "promès",
    },
    "empènyer": {
        PRESENT: ["empenyo", "empenys", "empeny", "empenyem", "empenyeu", "empenyen"],
        FUTUR: ["empenyeré", "empenyeràs", "empenyerà", "empenyerem", "empenyereu", "empenyeran"],
        PARTICIP: "empès",
    },
    "atènyer": {
        PRESENT: ["atenyo", "atenys", "ateny", "atenyem", "atenyeu", "atenyen"],
        PARTICIP: "atès",
    },
    "estrènyer": {
        PRESENT: ["estrenyo", "estrenys", "estreny", "estrenyem", "estrenyeu", "estrenyen"],
        PARTICIP: "estret",
    },
    "descriure": {
        PRESENT: ["descric", "descrius", "descriu", "descrivim", "descriviu", "descriuen"],
        PARTICIP: "descrit",
        GERUNDI: "descrivint",
    },
    "extreure": {
        PRESENT: ["extrec", "extreus", "extreu", "extraiem", "extraieu", "extreuen"],
        PARTICIP: "extret",
    },
    "sorprendre": {
        PRESENT: ["sorprenc", "sorprens", "sorprèn", "sorprenem", "sorpreneu", "sorprenen"],
        PARTICIP: "sorprès",
    },
    "suspendre": {
        PRESENT: ["suspenc", "suspens", "suspèn", "suspenem", "suspeneu", "suspenen"],
        PARTICIP: "suspès",
    },
    "estendre": {
        PRESENT: ["estenc", "estens", "estén", "estenem", "esteneu", "estenen"],
        PARTICIP: "estès",
    },
    "encendre": {
        PRESENT: ["encenc", "encens", "encén", "encenem", "enceneu", "encenen"],
        PARTICIP: "encès",
    },
    "absoldre": {
        PRESENT: ["absolc", "absols", "absol", "absolem", "absoleu", "absolen"],
        PARTICIP: "absolt",
    },
    "moldre": {
        PRESENT: ["molc", "mols", "mol", "molem", "moleu", "molen"],
        PARTICIP: "molt",
    },
    "romandre": {
        PRESENT: ["romanc", "romans", "roman", "romanem", "romaneu", "romanen"],
        PARTICIP: "romàs",
    },
    "retòrcer": {
        PRESENT: ["retorço", "retorces", "retorç", "retorcem", "retorceu", "retorcen"],
        PARTICIP: "retorçut",
    },
    "satisfer": {
        PRESENT: ["satisfaig", "satisfàs", "satisfà", "satisfem", "satisfeu", "satisfan"],
        PARTICIP: "satisfet",
    },
    "revendre": {
        PRESENT: ["revenc", "revens", "revèn", "revenem", "reveneu", "revenen"],
        PARTICIP: "revenut",
    },
    "descosir": {
        PRESENT: ["descuso", "descuses", "descús", "descosim", "descosiu", "descusen"],
        PARTICIP: "descosit",
    },
    "concloure": {
        PRESENT: ["concloc", "conclous", "conclou", "concloem", "concloeu", "conclouen"],
        PARTICIP: "conclòs",
    },
    "vindre": {
        PRESENT: ["vinc", "vens|véns", "ve|vé", "venim", "veniu", "venen|vénen"],
        PARTICIP: "vingut",
    },
    "caler": {
        PRESENT: ["-", "-", "cal", "-", "-", "calen"],
        PARTICIP: "calgut",
    },
    "dependre": {
        PRESENT: ["depenc", "depens", "depèn", "depenem", "depeneu", "depenen"],
        PARTICIP: "depès",
    },
    "constrènyer": {
        PRESENT: ["constrenyo", "constrenys", "constreny", "constrenyem", "constrenyeu", "constrenyen"],
        PARTICIP: "constret",
    },
    "malveure": {
        PRESENT: ["malveig", "malveus", "malveu", "malveiem", "malveieu", "malveuen"],
        PARTICIP: "malvist",
    },
}


def _regular_ar(stem):
    """The fully regular -ar paradigm, e.g. parlar -> parlo, parles, ...

    Used for the common regular verbs so they also count as verified; the
    irregular ones above are written out form by form.
    """
    return {
        PRESENT: [
            stem + "o", stem + "es", stem + "a",
            stem + "em", stem + "eu", stem + "en",
        ],
        IMPERFET: [
            stem + "ava", stem + "aves", stem + "ava",
            stem + "àvem", stem + "àveu", stem + "aven",
        ],
        FUTUR: [
            stem + "aré", stem + "aràs", stem + "arà",
            stem + "arem", stem + "areu", stem + "aran",
        ],
        PARTICIP: stem + "at",
        GERUNDI: stem + "ant",
    }


REFERENCE.update({
    verb: _regular_ar(verb[:-2])
    for verb in (
        "donar", "agafar", "comprar", "treballar", "escoltar", "acabar",
        "caminar", "esperar", "arribar", "entrar", "trobar", "pensar",
        "necessitar", "ajudar", "mirar", "portar", "deixar", "passar",
        "quedar", "preguntar",
    )
})

# tancar keeps the hard c sound, so the spelling changes before e and i
REFERENCE["tancar"] = {
    PRESENT: ["tanco", "tanques", "tanca", "tanquem", "tanqueu", "tanquen"],
    SUBJ_PRESENT: ["tanqui", "tanquis", "tanqui", "tanquem", "tanqueu", "tanquin"],
    PARTICIP: "tancat",
    GERUNDI: "tancant",
}


def variants(form):
    """Split a reference form into its acceptable spellings."""
    return [part for part in str(form).split("|") if part]


def matches(expected, actual):
    """True when *actual* is one of the spellings *expected* allows."""
    if expected is None:
        return True
    return actual in variants(expected)
