/* ============================================================
   TRANSLATIONS  –  FR / AR
   ============================================================ */
const translations = {
    fr: {
        /* Auth */
        org_name:           "CAISSE NATIONALE D'ASSURANCE MALADIE",
        org_name_ar:        "الصندوق الوطني للتأمين الصحي",
        login_title:        "Espace Assuré",
        email_label:        "Adresse e-mail",
        email_placeholder:  "Ex: votre@email.com",
        password_label:     "Mot de passe",
        password_placeholder: "Votre mot de passe",
        forgot_password:    "Mot de passe oublié ?",
        remember_me:        "Mémoriser mon identifiant",
        login_btn:          "Se connecter",
        no_account:         "Première visite sur le portail ou pas encore de compte ?",
        create_account_link:"Créer votre compte assuré",
        /* Register */
        register_title:     "Créer votre compte<br>CNAM Assuré",
        register_desc:      "Activez vos services numériques de santé en quelques étapes simples avec vos identifiants officiels.",
        verification_badge: "Vérification instantanée auprès du registre national d'assurance maladie",
        confirm_password:   "Confirmer le mot de passe",
        rule_chars:         "8+ car.",
        rule_case:          "Min/Maj",
        rule_num:           "Chiffre",
        terms_text:         "J'accepte expressément les",
        terms_link:         "Conditions Générales d'Utilisation",
        terms_text2:        "et consens au traitement de mes données de santé.",
        create_btn:         "Créer un compte",
        already_account:    "Vous possédez déjà un compte CNAM ?",
        /* Navbar */
        tab_portail:        "Portail Assuré",
        agent_access:       "Accès Agent",
        logout:             "Déconnexion",
        /* Dashboard – Section 1 */
        section1_title:     "1. Photo d'identité normalisée",
        required_badge:     "* REQUIS",
        upload_title:       "Glissez votre photo ou cliquez ici",
        upload_desc:        "Format carte d'identité ou passeport (JPG, PNG). Fond neutre, visage découvert, max 5 Mo.",
        select_file:        "Sélectionner un fichier",
        preview_text:       "Aperçu<br>35x45mm",
        official_format:    "Format officiel requis",
        /* Section 2 */
        section2_title:     "2. Identification nationale & CNAM",
        auto_verify:        "Vérification automatique",
        nni_label:          "NNI (Numéro National d'Identification)",
        nni_hint:           "0 / 10 chiffres",
        nni_placeholder:    "Ex: 1092837465",
        nni_help:           "Requis pour rattacher automatiquement vos droits ou générer votre immatriculation.",
        inam_label:         "Numéro d'Assuré INAM (Optionnel)",
        inam_help:          "Indiquez votre ancien numéro si vous avez déjà été assuré.",
        card_label:         "N° de Carte d'Assuré (Si disponible)",
        card_help:          "Numéro inscrit au dos ou sur la face de votre carte magnétique CNAM.",
        /* Section 3 */
        section3_title:     "3. État Civil & Coordonnées de Contact",
        sms_confirm:        "SMS de confirmation",
        lastname_label:     "Nom de famille",
        lastname_placeholder:"Ex: Ould Ahmed",
        firstname_label:    "Prénom",
        firstname_placeholder:"Ex: Mohamed Lemine",
        dob_label:          "Date de naissance",
        dob_placeholder:    "jj/mm/aaaa",
        age_label:          "Âge de l'assuré (Automatique)",
        age_placeholder:    "-- ans",
        waiting_date:       "En attente de date",
        phone_label:        "Téléphone portable (Notification SMS)",
        phone_hint:         "Numéro actif pour recevoir votre code de suivi",
        /* Section 4 */
        section4_title:     "4. Motif & Précisions de la demande",
        free_zone:          "Zone libre",
        motif1:             "Nouvelle affiliation",
        motif2:             "Prise en charge / ALD",
        motif3:             "Renouvellement de carte",
        details_label:      "Détails médicaux, antécédents, structure sanitaire ou motif particulier :",
        details_placeholder:"Indiquez ici toute information utile à la commission médicale ou au guichet d'affiliation...",
        secure_text:        "Transmission directe sécurisée avec certificat d'État.",
        submit_btn:         "Envoyer la demande",
        /* Info card */
        info_card_title:    "Caisse Nationale d'Assurance Maladie",
        info_card_desc:     "Le service de dépôt direct sans authentification permet d'engager un traitement prioritaire de votre dossier sous 48 heures ouvrables.",
        /* Recherche de l'assuré (NNI / INAM) et Feuille de soins PDF */
        verify_assure_btn:  "Vérifier",
        assure_found_badge: "ASSURÉ TROUVÉ",
        assure_not_found_title: "Assuré introuvable",
        lbl_nni:            "NNI",
        lbl_inam:           "N° d'Assuré INAM",
        lbl_numero_carte:   "N° de carte",
        lbl_naissance:      "Date de naissance",
        lbl_age:            "Âge",
        lbl_sexe:           "Sexe",
        lbl_telephone:      "Téléphone",
        lbl_numero_feuille: "N° de feuille de soins",
        unit_years:         "ans",
        msg_identifiant_required: "Saisissez un NNI ou un numéro d'Assuré INAM.",
        msg_verification_en_cours: "Vérification dans la base de l'assurance maladie…",
        msg_assure_trouve:  "Assuré trouvé. Votre Feuille de soins a été générée et le téléchargement démarre.",
        msg_assure_photo_absente: "Aucune photo enregistrée pour cet assuré.",
        msg_date_soins:     "Date des soins : ",
        msg_feuille_numero: "Feuille n° ",
        /* Liste des établissements de santé conventionnés */
        etablissement_label:    "HÔPITAL OU CENTRE DE SANTÉ",
        etablissement_placeholder: "Rechercher un établissement par nom (ex : Cheikh Zaid)",
        etablissement_option:   "— Sélectionner un établissement conventionné —",
        etablissement_aucun:    "Aucun établissement ne correspond à cette recherche.",
        etablissement_indisponible: "Liste des établissements indisponible.",
        etablissement_aide:     "L'établissement sélectionné est inscrit automatiquement sur votre Feuille de soins.",
        lbl_centre_hospitalier: "Établissement",
        msg_etablissement_associe: "Établissement associé à la Feuille de soins : ",
        msg_etablissement_requis: "Sélectionnez d'abord un hôpital ou un centre de santé : ce choix est obligatoire avant de saisir le NNI ou l'INAM.",
        /* Compléments : textes présents dans les pages */
        page_title:         "CNAM - Espace Assuré",
        register_line1:     "Créer votre compte",
        register_line2:     "CNAM Assuré",
        rule_case_long:     "Minuscule Majuscule",
        terms_privacy:      "et consens au traitement de mes données de santé à caractère personnel conformément aux réglementations de protection sanitaire.",
        preview_line1:      "Aperçu",
        preview_line2:      "35x45mm",
        phone_label_short:  "Téléphone portable",
        nni_hint_short:     "10 chiffres pour le NNI",
        /* Compléments : placeholders */
        reg_email_placeholder: "votre@email.com",
        inam_placeholder:   "Ex: 8472910-B",
        card_placeholder:   "Ex: CN-9948271",
        details_placeholder_long: "Indiquez ici toute information utile à la commission médicale ou au guichet d'affiliation (ex: nom de l'hôpital, prescription urgente, motif de rattachement...)",
        search_placeholder: "Ex: 1849204812",
        /* Messages des formulaires */
        msg_email_required: "Saisissez votre adresse e-mail.",
        msg_password_required: "Saisissez votre mot de passe.",
        msg_password_short: "Le mot de passe doit comporter au moins 8 caractères.",
        msg_password_mismatch: "Les mots de passe ne correspondent pas.",
        msg_terms_required: "Veuillez accepter les Conditions Générales d'Utilisation pour créer votre compte.",
        msg_network_error:  "Impossible de contacter le serveur CNAM. Vérifiez que « python manage.py runserver » est bien démarré puis réessayez.",
        msg_csrf_error:     "Session expirée (protection CSRF). Rechargez la page puis réessayez.",
        msg_api_missing:    "L'API est introuvable. Redémarrez Django puis actualisez la page.",
        /* Photo d'identité */
        msg_photo_type:     "Format non pris en charge. Choisissez une image JPG ou PNG.",
        msg_photo_size:     "La photo dépasse 5 Mo. Choisissez un fichier plus léger.",
        msg_photo_selected: "Photo importée avec succès.",
        msg_photo_read_error: "Lecture du fichier impossible. Essayez une autre image.",
        remove_photo_btn:   "Supprimer la photo",
    },
    ar: {
        /* Auth */
        org_name:           "الصندوق الوطني للتأمين الصحي",
        org_name_ar:        "الصندوق الوطني للتأمين الصحي",
        login_title:        "فضاء المؤمَّن",
        email_label:        "البريد الإلكتروني",
        email_placeholder:  "مثال: بريدك@email.com",
        password_label:     "كلمة المرور",
        password_placeholder:"كلمة المرور الخاصة بك",
        forgot_password:    "نسيت كلمة المرور؟",
        remember_me:        "تذكر معرفي",
        login_btn:          "تسجيل الدخول",
        no_account:         "زيارتك الأولى للبوابة أو ليس لديك حساب بعد؟",
        create_account_link:"إنشاء حساب المؤمَّن",
        /* Register */
        register_title:     "إنشاء حسابك<br>لدى الصندوق الوطني",
        register_desc:      "فعّل خدماتك الرقمية الصحية في خطوات بسيطة باستخدام معرفاتك الرسمية.",
        verification_badge: "تحقق فوري من السجل الوطني للتأمين الصحي",
        confirm_password:   "تأكيد كلمة المرور",
        rule_chars:         "+٨ أحرف",
        rule_case:          "كبير/صغير",
        rule_num:           "رقم",
        terms_text:         "أوافق صراحةً على",
        terms_link:         "الشروط العامة للاستخدام",
        terms_text2:        "وأقبل معالجة بياناتي الصحية.",
        create_btn:         "إنشاء حساب",
        already_account:    "هل لديك حساب لدى الصندوق بالفعل؟",
        /* Navbar */
        tab_portail:        "بوابة المؤمَّن",
        agent_access:       "دخول الوكيل",
        logout:             "تسجيل الخروج",
        /* Section 1 */
        section1_title:     "١. صورة الهوية المعيارية",
        required_badge:     "* مطلوب",
        upload_title:       "اسحب صورتك أو انقر هنا",
        upload_desc:        "صيغة بطاقة الهوية أو جواز السفر (JPG، PNG). خلفية محايدة، وجه مكشوف، الحد الأقصى ٥ ميغابايت.",
        select_file:        "اختيار ملف",
        preview_text:       "معاينة<br>35×45 ملم",
        official_format:    "الصيغة الرسمية مطلوبة",
        /* Section 2 */
        section2_title:     "٢. التعريف الوطني والصندوق",
        auto_verify:        "تحقق تلقائي",
        nni_label:          "رقم التعريف الوطني (NNI)",
        nni_hint:           "١٠ أرقام",
        nni_placeholder:    "مثال: 1092837465",
        nni_help:           "مطلوب لربط حقوقك تلقائياً أو توليد تسجيلك.",
        inam_label:         "رقم المؤمَّن لدى INAM (اختياري)",
        inam_help:          "أدخل رقمك القديم إذا كنت مؤمَّناً سابقاً.",
        card_label:         "رقم بطاقة المؤمَّن (إن توفر)",
        card_help:          "الرقم المدوّن على ظهر أو واجهة بطاقتك المغناطيسية.",
        /* Section 3 */
        section3_title:     "٣. الحالة المدنية وبيانات الاتصال",
        sms_confirm:        "رسالة SMS للتأكيد",
        lastname_label:     "اللقب",
        lastname_placeholder:"مثال: ولد أحمد",
        firstname_label:    "الاسم الأول",
        firstname_placeholder:"مثال: محمد الأمين",
        dob_label:          "تاريخ الميلاد",
        dob_placeholder:    "يي/شش/سسسس",
        age_label:          "عمر المؤمَّن (تلقائي)",
        age_placeholder:    "-- سنة",
        waiting_date:       "في انتظار التاريخ",
        phone_label:        "الهاتف المحمول (إشعار SMS)",
        phone_hint:         "رقم نشط لاستلام رمز المتابعة",
        /* Section 4 */
        section4_title:     "٤. سبب الطلب وتفاصيله",
        free_zone:          "منطقة حرة",
        motif1:             "انتساب جديد",
        motif2:             "تكفل / مرض مزمن",
        motif3:             "تجديد البطاقة",
        details_label:      "التفاصيل الطبية والسوابق والمنشأة الصحية أو السبب الخاص:",
        details_placeholder:"أدخل هنا أي معلومات مفيدة للجنة الطبية أو مكتب الانتساب...",
        secure_text:        "إرسال مباشر آمن بشهادة الدولة.",
        submit_btn:         "إرسال الطلب",
        /* Info card */
        info_card_title:    "الصندوق الوطني للتأمين الصحي",
        info_card_desc:     "تتيح خدمة الإيداع المباشر دون مصادقة فتح معالجة ذات أولوية لملفك خلال ٤٨ ساعة عمل.",
        /* Recherche de l'assuré (NNI / INAM) et Feuille de soins PDF */
        verify_assure_btn:  "تحقّق",
        assure_found_badge: "المؤمَّن موجود",
        assure_not_found_title: "المؤمَّن غير موجود",
        lbl_nni:            "الرقم الوطني للتعريف",
        lbl_inam:           "رقم المؤمَّن INAM",
        lbl_numero_carte:   "رقم البطاقة",
        lbl_naissance:      "تاريخ الميلاد",
        lbl_age:            "العمر",
        lbl_sexe:           "الجنس",
        lbl_telephone:      "الهاتف",
        lbl_numero_feuille: "رقم ورقة العلاج",
        unit_years:         "سنة",
        msg_identifiant_required: "أدخل الرقم الوطني للتعريف أو رقم المؤمَّن INAM.",
        msg_verification_en_cours: "جارٍ التحقق في قاعدة بيانات التأمين الصحي…",
        msg_assure_trouve:  "تم العثور على المؤمَّن. تم إنشاء ورقة العلاج وبدأ التحميل.",
        msg_assure_photo_absente: "لا توجد صورة مسجّلة لهذا المؤمَّن.",
        msg_date_soins:     "تاريخ العلاج: ",
        msg_feuille_numero: "ورقة رقم ",
        /* قائمة المؤسسات الصحية المتعاقدة */
        etablissement_label:    "المستشفى أو مركز الصحة",
        etablissement_placeholder: "ابحث عن مؤسسة بالاسم (مثال: شيخ زايد)",
        etablissement_option:   "— اختر مؤسسة متعاقدة —",
        etablissement_aucun:    "لا توجد مؤسسة مطابقة لهذا البحث.",
        etablissement_indisponible: "قائمة المؤسسات غير متاحة.",
        etablissement_aide:     "تُسجَّل المؤسسة المختارة تلقائياً في ورقة العلاج الخاصة بكم.",
        lbl_centre_hospitalier: "المؤسسة",
        msg_etablissement_associe: "المؤسسة المرتبطة بورقة العلاج: ",
        msg_etablissement_requis: "اختر أولاً المستشفى أو مركز الصحة: هذا الاختيار إلزامي قبل إدخال رقم التعريف الوطني أو رقم المؤمَّن.",
        /* Compléments : textes présents dans les pages */
        page_title:         "CNAM - فضاء المؤمَّن",
        register_line1:     "إنشاء حسابك",
        register_line2:     "لدى الصندوق الوطني",
        rule_case_long:     "كبير/صغير",
        terms_privacy:      "وأوافق على معالجة بياناتي الصحية ذات الطابع الشخصي وفقاً للأنظمة الصحية.",
        preview_line1:      "معاينة",
        preview_line2:      "35×45 ملم",
        phone_label_short:  "الهاتف المحمول",
        nni_hint_short:     "١٠ أرقام لرقم التعريف الوطني",
        /* Compléments : placeholders */
        reg_email_placeholder: "بريدك@email.com",
        inam_placeholder:   "مثال: 8472910-B",
        card_placeholder:   "مثال: CN-9948271",
        details_placeholder_long: "أدخل هنا أي معلومات مفيدة للجنة الطبية أو مكتب الانتساب (مثال: اسم المستشفى، وصفة عاجلة، سبب الانتساب...)",
        search_placeholder: "مثال: 1849204812",
        /* Messages des formulaires */
        msg_email_required: "أدخل بريدك الإلكتروني.",
        msg_password_required: "أدخل كلمة المرور.",
        msg_password_short: "يجب أن تتكون كلمة المرور من ٨ أحرف على الأقل.",
        msg_password_mismatch: "كلمتا المرور غير متطابقتين.",
        msg_terms_required: "يرجى الموافقة على شروط الاستخدام لإنشاء حسابك.",
        msg_network_error:  "تعذّر الاتصال بخادم الصندوق. تأكد من تشغيل « python manage.py runserver » ثم أعد المحاولة.",
        msg_csrf_error:     "انتهت صلاحية الجلسة (حماية CSRF). أعد تحميل الصفحة ثم حاول مرة أخرى.",
        msg_api_missing:    "لم يتم العثور على واجهة البرمجة. أعد تشغيل Django ثم حدّث الصفحة.",
        /* Photo d'identité */
        msg_photo_type:     "صيغة غير مدعومة. اختر صورة بصيغة JPG أو PNG.",
        msg_photo_size:     "حجم الصورة يتجاوز ٥ ميغابايت. اختر ملفاً أصغر.",
        msg_photo_selected: "تم استيراد الصورة بنجاح.",
        msg_photo_read_error: "تعذّر قراءة الملف. جرّب صورة أخرى.",
        remove_photo_btn:   "حذف الصورة",
    }
};

/* ============================================================
   INDEX AUTOMATIQUE  FR -> AR
   Construit à partir du dictionnaire ci-dessus : chaque texte
   français connu est associé à sa traduction arabe. Cela permet de
   traduire toute la page (y compris les textes sans data-i18n).
   ============================================================ */
function normalizeText(value) {
    return String(value == null ? '' : value).replace(/\s+/g, ' ').trim();
}

const frToAr = (() => {
    const index = {};
    const fr = translations.fr;
    const ar = translations.ar;

    Object.keys(fr).forEach(key => {
        const source = fr[key];
        const target = ar[key];
        if (typeof source !== 'string' || typeof target !== 'string') return;
        if (source.includes('<') || target.includes('<')) return;   // balises HTML
        const normalized = normalizeText(source);
        if (normalized) index[normalized] = target;
    });

    return index;
})();

/* Mémoire des textes d'origine (pour revenir au français) */
const originalTexts = new WeakMap();
const originalPlaceholders = new WeakMap();

function textNodesIn(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode(node) {
            const parent = node.parentElement;
            if (!parent || ['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(parent.tagName)) {
                return NodeFilter.FILTER_REJECT;
            }
            return normalizeText(node.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
        },
    });

    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    return nodes;
}

/* Traduit (ou restaure) les textes visibles de la page */
function translatePageTexts(dictionary) {
    textNodesIn(document.body).forEach(node => {
        if (!originalTexts.has(node)) originalTexts.set(node, node.nodeValue);

        const original = originalTexts.get(node);

        if (!dictionary) {
            if (node.nodeValue !== original) node.nodeValue = original;
            return;
        }

        const translated = dictionary[normalizeText(original)];
        if (translated === undefined) return;

        const leading = original.match(/^\s*/)[0];
        const trailing = original.match(/\s*$/)[0];
        node.nodeValue = leading + translated + trailing;
    });
}

/* Traduit (ou restaure) les placeholders des champs de saisie */
function translatePagePlaceholders(dictionary) {
    document.querySelectorAll('[placeholder]').forEach(element => {
        if (!originalPlaceholders.has(element)) {
            originalPlaceholders.set(element, element.getAttribute('placeholder'));
        }

        const original = originalPlaceholders.get(element);

        if (!dictionary) {
            element.setAttribute('placeholder', original);
            return;
        }

        const translated = dictionary[normalizeText(original)];
        if (translated !== undefined) element.setAttribute('placeholder', translated);
    });
}

/* Traduit l'onglet du navigateur */
function translatePageTitle(dictionary) {
    const original = translatePageTitle.original || document.title;
    translatePageTitle.original = original;

    const translated = dictionary ? dictionary[normalizeText(original)] : undefined;
    document.title = translated || original;
}

/* ============================================================
   CURRENT LANGUAGE STATE
   ============================================================ */
let currentLang = 'fr';

/* Retourne la traduction d'une clé dans la langue courante */
function t(key) {
    const dictionary = translations[currentLang] || translations.fr;
    return dictionary[key] || translations.fr[key] || key;
}

/* ============================================================
   setLang  –  switches language and applies translations
   ============================================================ */
function setLang(lang) {
    currentLang = lang;
    const t = translations[lang];
    const isRTL = (lang === 'ar');

    /* 1. html attributes */
    const html = document.getElementById('html-root');
    html.lang = lang;
    html.dir  = isRTL ? 'rtl' : 'ltr';

    /* 2. body font */
    document.body.style.fontFamily = isRTL
        ? "'Cairo', sans-serif"
        : "'Inter', sans-serif";

    /* 3. translate text nodes */
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key] !== undefined) {
            el.innerHTML = t[key];
        }
    });

    /* 3bis. traduction automatique de tous les textes de la page */
    translatePageTexts(currentLang === 'fr' ? null : frToAr);
    translatePagePlaceholders(currentLang === 'fr' ? null : frToAr);
    translatePageTitle(currentLang === 'fr' ? null : frToAr);

    /* 4. translate placeholder attributes */
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (t[key] !== undefined) {
            el.placeholder = t[key];
        }
    });

    /* Navigation labels do not use data-i18n attributes. */
    const portailTab = document.getElementById('btn-portail-tab');
    const agentButton = document.querySelector('.btn-agent');
    if (portailTab) portailTab.textContent = t.tab_portail;
    if (agentButton) agentButton.textContent = t.agent_access;

    /* 5. directional arrow icons  */
    document.querySelectorAll('.btn-icon-dir').forEach(icon => {
        icon.className = isRTL
            ? 'fa-solid fa-arrow-left btn-icon-dir'
            : 'fa-solid fa-arrow-right btn-icon-dir';
    });

    /* 6. update auth-page lang switcher buttons */
    const btnFr = document.getElementById('btn-fr');
    const btnAr = document.getElementById('btn-ar');
    if (btnFr && btnAr) {
        btnFr.classList.toggle('active', lang === 'fr');
        btnAr.classList.toggle('active', lang === 'ar');
    }

    /* 7. update navbar lang switcher buttons */
    const navBtnFr = document.getElementById('nav-btn-fr');
    const navBtnAr = document.getElementById('nav-btn-ar');
    if (navBtnFr && navBtnAr) {
        navBtnFr.classList.toggle('active', lang === 'fr');
        navBtnAr.classList.toggle('active', lang === 'ar');
    }

    /* 8. persist choice */
    localStorage.setItem('cnam_lang', lang);
}

/* ============================================================
   On load – restore saved language preference
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('cnam_lang') || 'fr';
    setLang(saved);
    updatePasswordRules();
    initPhotoUpload();
    initRechercheAssure();
    initEtablissements();
});

/* ============================================================
   API – REQUÊTES JSON
   ============================================================ */
function getCsrfToken() {
    const match = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : '';
}

/* Message d'erreur / de succès affiché dans un formulaire */
function showAuthMessage(elementId, message, isError = false) {
    const element = document.getElementById(elementId);
    if (!element) {
        if (isError) alert(message);
        return;
    }
    element.textContent = message;
    element.style.color = isError ? '#c81e4f' : 'var(--success-color)';
}

function clearAuthMessage(elementId) {
    showAuthMessage(elementId, '');
}

/* Affiche l'adresse e-mail de l'assuré connecté dans le menu profil */
function setConnectedUser(email) {
    const element = document.getElementById('profile-user-email');
    if (element) element.textContent = email || '';
}

/* Règles du mot de passe affichées en direct sous le champ */
function toggleRule(ruleId, isValid) {
    const rule = document.getElementById(ruleId);
    if (rule) rule.classList.toggle('valid', isValid);
}

function updatePasswordRules() {
    const input = document.getElementById('reg-password');
    const password = input ? input.value : '';

    toggleRule('rule-length', password.length >= 8);
    toggleRule('rule-case', /[a-z]/.test(password) && /[A-Z]/.test(password));
    toggleRule('rule-digit', /\d/.test(password));
}

/* Requête GET JSON (liste des établissements de santé conventionnés). */
async function apiGet(url) {
    let response;

    try {
        response = await fetch(url, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
        });
    } catch (networkError) {
        throw new Error(t('msg_network_error'));
    }

    const responseText = await response.text();
    let data;

    try {
        data = JSON.parse(responseText);
    } catch {
        throw new Error(`Le serveur a renvoyé une réponse invalide (HTTP ${response.status}). Redémarrez Django puis actualisez la page.`);
    }

    if (!response.ok) {
        throw new Error(data.error || `Une erreur est survenue (HTTP ${response.status}).`);
    }

    return data;
}

async function apiRequest(url, payload) {
    let response;

    try {
        response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify(payload),
        });
    } catch (networkError) {
        // Le serveur Django n'est pas joignable (arrêté, redémarré ou hors ligne).
        throw new Error(t('msg_network_error'));
    }

    const responseText = await response.text();
    let data;

    try {
        data = JSON.parse(responseText);
    } catch {
        if (response.status === 403) {
            throw new Error(t('msg_csrf_error'));
        }
        if (response.status === 404) {
            throw new Error(t('msg_api_missing'));
        }
        throw new Error(`Le serveur a renvoyé une réponse invalide (HTTP ${response.status}). Redémarrez Django puis actualisez la page.`);
    }

    if (!response.ok) {
        throw new Error(data.error || `Une erreur est survenue (HTTP ${response.status}).`);
    }

    return data;
}

/* ============================================================
   INSCRIPTION  (e-mail + mot de passe, sans code OTP)
   ============================================================ */
async function handleRegistration(event) {
    event.preventDefault();

    const email        = document.getElementById('reg-email').value.trim();
    const password     = document.getElementById('reg-password').value;
    const confirmation = document.getElementById('reg-confirm').value;
    const terms        = document.getElementById('terms');
    const submitButton = document.getElementById('register-submit');

    clearAuthMessage('register-message');

    if (!email) {
        showAuthMessage('register-message', t('msg_email_required'), true);
        return;
    }
    if (password.length < 8) {
        showAuthMessage('register-message', t('msg_password_short'), true);
        return;
    }
    if (password !== confirmation) {
        showAuthMessage('register-message', t('msg_password_mismatch'), true);
        return;
    }
    if (terms && !terms.checked) {
        showAuthMessage('register-message', t('msg_terms_required'), true);
        return;
    }

    if (submitButton) submitButton.disabled = true;

    try {
        const data = await apiRequest('/api/register/', {
            email,
            password,
            password_confirm: confirmation,
        });

        showAuthMessage('register-message', data.message, false);

        // Le compte est créé et la session ouverte : accès direct à l'espace assuré.
        document.getElementById('reg-email').value    = '';
        document.getElementById('reg-password').value = '';
        document.getElementById('reg-confirm').value  = '';
        updatePasswordRules();

        setConnectedUser(data.email || email);
        showDashboard();
    } catch (error) {
        showAuthMessage('register-message', error.message, true);
    } finally {
        if (submitButton) submitButton.disabled = false;
    }
}

/* ============================================================
   CONNEXION  (e-mail + mot de passe)
   ============================================================ */
async function handleLogin(event) {
    event.preventDefault();

    const email        = document.getElementById('login-email').value.trim();
    const password     = document.getElementById('login-password').value;
    const submitButton = document.getElementById('login-submit');

    clearAuthMessage('login-message');

    if (!email) {
        showAuthMessage('login-message', t('msg_email_required'), true);
        return;
    }
    if (!password) {
        showAuthMessage('login-message', t('msg_password_required'), true);
        return;
    }

    if (submitButton) submitButton.disabled = true;

    try {
        const data = await apiRequest('/api/login/', { email, password });

        document.getElementById('login-password').value = '';
        setConnectedUser(data.email || email);
        showDashboard();
    } catch (error) {
        showAuthMessage('login-message', error.message, true);
    } finally {
        if (submitButton) submitButton.disabled = false;
    }
}

/* ============================================================
   PASSWORD TOGGLE
   ============================================================ */
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const btn   = input.parentElement.querySelector('.toggle-password');
    const icon  = btn ? btn.querySelector('i') : null;

    if (input.type === 'password') {
        input.type = 'text';
        if (icon) { icon.classList.replace('fa-eye', 'fa-eye-slash'); }
    } else {
        input.type = 'password';
        if (icon) { icon.classList.replace('fa-eye-slash', 'fa-eye'); }
    }
}

/* ============================================================
   AUTH VIEW SWITCH  (login ↔ register)
   ============================================================ */
function switchAuthView(viewId) {
    const currentView = document.querySelector('#auth-container .card:not(.hidden)');
    const newView = document.getElementById(viewId);
    if (!currentView || !newView) return;

    currentView.style.opacity   = '0';
    currentView.style.transform = 'scale(0.98)';

    setTimeout(() => {
        currentView.classList.add('hidden');
        newView.classList.remove('hidden');

        newView.style.opacity   = '0';
        newView.style.transform = 'scale(1.02)';
        void newView.offsetWidth;

        newView.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        newView.style.opacity    = '1';
        newView.style.transform  = 'scale(1)';

        setTimeout(() => {
            currentView.style = '';
            newView.style     = '';
        }, 300);
    }, 200);
}

/* ============================================================
   PHOTO D'IDENTITÉ – import, aperçu et glisser-déposer
   ============================================================ */
const PHOTO_MAX_BYTES = 5 * 1024 * 1024;                        // 5 Mo
const PHOTO_ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png'];

function showPhotoMessage(message, isError = false) {
    showAuthMessage('photo-message', message, isError);
}

function renderPhotoPreview(file) {
    const preview = document.getElementById('photo-preview');
    const removeButton = document.getElementById('photo-remove-btn');
    if (!preview) return;

    const reader = new FileReader();

    reader.onload = event => {
        preview.innerHTML = '';
        const image = document.createElement('img');
        image.src = event.target.result;
        image.alt = file.name;
        preview.appendChild(image);
        if (removeButton) removeButton.classList.remove('hidden');
    };
    reader.onerror = () => showPhotoMessage(t('msg_photo_read_error'), true);
    reader.readAsDataURL(file);
}

function clearPhotoPreview() {
    const preview = document.getElementById('photo-preview');
    const input = document.getElementById('photo-input');
    const removeButton = document.getElementById('photo-remove-btn');

    if (preview) preview.innerHTML = '<i class="fa-solid fa-user"></i><span>Aperçu<br>35x45mm</span>';
    if (input) input.value = '';
    if (removeButton) removeButton.classList.add('hidden');
    showPhotoMessage('');
}

function handlePhotoFile(file) {
    if (!file) return;

    if (!PHOTO_ALLOWED_TYPES.includes(String(file.type).toLowerCase())) {
        showPhotoMessage(t('msg_photo_type'), true);
        return;
    }
    if (file.size > PHOTO_MAX_BYTES) {
        showPhotoMessage(t('msg_photo_size'), true);
        return;
    }

    renderPhotoPreview(file);
    showPhotoMessage(t('msg_photo_selected'));
}

function initPhotoUpload() {
    const zone = document.getElementById('photo-drop-zone');
    const input = document.getElementById('photo-input');
    const selectButton = document.getElementById('photo-select-btn');
    const removeButton = document.getElementById('photo-remove-btn');
    if (!zone || !input) return;

    const openPicker = () => input.click();

    zone.addEventListener('click', openPicker);
    zone.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            openPicker();
        }
    });

    if (selectButton) {
        selectButton.addEventListener('click', event => {
            event.stopPropagation();
            openPicker();
        });
    }

    if (removeButton) {
        removeButton.addEventListener('click', event => {
            event.stopPropagation();
            clearPhotoPreview();
        });
    }

    input.addEventListener('change', () => {
        if (input.files && input.files.length) handlePhotoFile(input.files[0]);
        input.value = '';   // permet de re-sélectionner le même fichier
    });

    ['dragenter', 'dragover'].forEach(type => zone.addEventListener(type, event => {
        event.preventDefault();
        zone.classList.add('is-dragover');
    }));

    ['dragleave', 'drop'].forEach(type => zone.addEventListener(type, event => {
        event.preventDefault();
        zone.classList.remove('is-dragover');
    }));

    zone.addEventListener('drop', event => {
        const files = event.dataTransfer ? event.dataTransfer.files : null;
        if (files && files.length) handlePhotoFile(files[0]);
    });
}

/* ============================================================
   RECHERCHE DE L'ASSURÉ (NNI / INAM) → FEUILLE DE SOINS PDF
   ============================================================ */
let feuilleSoinsCourante = null;

/* Vide les zones de résultat avant chaque nouvelle vérification. */
function reinitialiserResultatAssure() {
    const resultat = document.getElementById('assure-resultat');
    const erreur   = document.getElementById('assure-introuvable');
    const photo    = document.getElementById('assure-photo');
    const zone     = document.getElementById('assure-photo-zone');
    const infos    = document.getElementById('assure-infos');

    if (resultat) resultat.classList.add('hidden');
    if (erreur) erreur.classList.add('hidden');
    if (zone) zone.classList.add('hidden');
    if (photo) photo.removeAttribute('src');
    if (infos) infos.innerHTML = '';

    ['assure-nom-complet', 'assure-numero-feuille', 'assure-date-soins'].forEach(id => {
        const element = document.getElementById(id);
        if (element) element.textContent = '';
    });

    feuilleSoinsCourante = null;
}

/* Ajoute une ligne « libellé / valeur » dans la fiche de l'assuré. */
function ajouterInfoAssure(libelle, valeur) {
    const liste = document.getElementById('assure-infos');
    if (!liste || !valeur) return;

    const terme = document.createElement('dt');
    terme.textContent = libelle;

    const definition = document.createElement('dd');
    definition.textContent = valeur;

    liste.appendChild(terme);
    liste.appendChild(definition);
}

function afficherAssureTrouve(data) {
    const assure   = data.assure || {};
    const resultat = document.getElementById('assure-resultat');
    const erreur   = document.getElementById('assure-introuvable');
    const nom      = document.getElementById('assure-nom-complet');
    const numero   = document.getElementById('assure-numero-feuille');
    const date     = document.getElementById('assure-date-soins');
    const zone     = document.getElementById('assure-photo-zone');
    const photo    = document.getElementById('assure-photo');

    /* Exclusivité des résultats : jamais « trouvé » et « introuvable » ensemble. */
    if (erreur) erreur.classList.add('hidden');

    if (nom) nom.textContent = assure.nom_complet || '';
    if (numero) numero.textContent = t('msg_feuille_numero') + (data.numero_feuille || '');
    if (date) date.textContent = t('msg_date_soins') + (data.date_soins || '');

    ajouterInfoAssure(t('lbl_nni'), assure.nni);
    ajouterInfoAssure(t('lbl_inam'), assure.inam);
    ajouterInfoAssure(t('lbl_numero_carte'), assure.numero_carte);
    ajouterInfoAssure(t('lbl_naissance'), assure.date_naissance);
    ajouterInfoAssure(t('lbl_age'), assure.age ? `${assure.age} ${t('unit_years')}` : '');
    ajouterInfoAssure(t('lbl_sexe'), assure.sexe);
    ajouterInfoAssure(t('lbl_telephone'), assure.telephone);
    ajouterInfoAssure(t('lbl_centre_hospitalier'), assure.centre_hospitalier);

    /* Photo de profil : affichée uniquement si elle existe dans PostgreSQL. */
    if (data.photo_disponible && photo && zone) {
        photo.src = data.photo_url;
        photo.alt = assure.nom_complet || '';
        zone.classList.remove('hidden');
    }

    feuilleSoinsCourante = { url: data.feuille_url, nom: data.feuille_nom };
    if (resultat) resultat.classList.remove('hidden');
}

function afficherAssureIntrouvable(message) {
    const resultat = document.getElementById('assure-resultat');
    const erreur   = document.getElementById('assure-introuvable');
    const titre    = document.getElementById('assure-erreur-titre');
    const texte    = document.getElementById('assure-erreur-texte');

    /* Exclusivité des résultats : masque le bloc « Assuré trouvé ». */
    if (resultat) resultat.classList.add('hidden');

    if (titre) titre.textContent = t('assure_not_found_title');
    if (texte) texte.textContent = message || '';
    if (erreur) erreur.classList.remove('hidden');
}

/* Lance le téléchargement du PDF de la feuille de soins.

   On passe par un lien temporaire porteur de l'attribut `download` plutôt que
   par `window.location.href` : ce dernier fait quitter la page au navigateur,
   ce qui détruit le résultat de la recherche (nom, NNI, photo…) juste après
   son affichage et donne l'impression que rien ne s'affiche. */
function telechargerFeuilleSoins() {
    if (!feuilleSoinsCourante) return;

    const lien = document.createElement('a');
    lien.href = feuilleSoinsCourante.url;
    lien.download = feuilleSoinsCourante.nom || '';
    lien.rel = 'noopener';
    lien.style.display = 'none';

    document.body.appendChild(lien);
    lien.click();
    document.body.removeChild(lien);
}

/* Bouton « Vérifier » : recherche l'assuré puis génère sa Feuille de soins. */
async function verifierAssure() {
    const champ = document.getElementById('assure-identifiant');
    const bouton = document.getElementById('btn-verifier-assure');
    const identifiant = champ ? champ.value.trim() : '';

    /* Sécurité : même appelée au clavier, la vérification exige un hôpital. */
    if (!etablissementSelectionne()) {
        showAuthMessage('verification-message', t('msg_etablissement_requis'), true);
        majEtatChampIdentifiant();
        const selectEtab = document.getElementById('etablissement-select');
        if (selectEtab) selectEtab.focus();
        return;
    }

    if (!identifiant) {
        showAuthMessage('verification-message', t('msg_identifiant_required'), true);
        if (champ) champ.focus();
        return;
    }

    reinitialiserResultatAssure();
    showAuthMessage('verification-message', t('msg_verification_en_cours'));
    if (bouton) bouton.disabled = true;

    try {
        const data = await apiRequest('/api/assures/verifier/', {
            identifiant: identifiant,
            etablissement: etablissementSelectionne(),
        });
        afficherAssureTrouve(data);

        const association = data.etablissement_selectionne
            ? `${t('msg_etablissement_associe')}${data.etablissement_selectionne}.`
            : '';
        showAuthMessage('verification-message',
            association ? `${t('msg_assure_trouve')} ${association}` : t('msg_assure_trouve'));

        telechargerFeuilleSoins();     // téléchargement automatique de la feuille
    } catch (error) {
        afficherAssureIntrouvable(error.message);
        showAuthMessage('verification-message', error.message, true);
    } finally {
        /* L'état du bouton suit la sélection d'hôpital, pas l issu de l'appel. */
        majEtatChampIdentifiant();
    }
}

/* ============================================================
   ÉTABLISSEMENTS DE SANTÉ CONVENTIONNÉS
   Liste déroulante alimentée par /api/etablissements/ avec
   recherche par nom. L'établissement choisi est renvoyé lors de
   la vérification : il est alors inscrit sur la Feuille de soins.
   ============================================================ */
let etablissementsListe = [];           // résultat de la dernière recherche
let rechercheEtablissementTimer = null;  // anti-rebond de la recherche

/* Remplit la liste déroulante en conservant la sélection courante. */
function remplirSelectEtablissements(etablissements) {
    const select = document.getElementById('etablissement-select');
    if (!select) return;

    etablissementsListe = etablissements || [];
    const selectionCourante = select.value;
    select.innerHTML = '';

    if (!etablissementsListe.length) {
        const aucune = document.createElement('option');
        aucune.value = '';
        aucune.textContent = t('etablissement_aucun');
        select.appendChild(aucune);
        select.disabled = true;
        return;
    }

    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = t('etablissement_option');
    select.appendChild(placeholder);

    etablissementsListe.forEach(etablissement => {
        const option = document.createElement('option');
        option.value = String(etablissement.id);
        option.textContent = etablissement.libelle || etablissement.nom;
        select.appendChild(option);
    });

    select.disabled = false;

    /* La sélection survit au filtrage si l'établissement est toujours listé. */
    if (selectionCourante
        && etablissementsListe.some(e => String(e.id) === selectionCourante)) {
        select.value = selectionCourante;
    }
}

/* Charge la liste depuis l'API (recherche par nom côté serveur). */
async function chargerEtablissements(requete = '') {
    const select = document.getElementById('etablissement-select');

    try {
        const data = await apiGet(`/api/etablissements/?q=${encodeURIComponent(requete)}`);
        remplirSelectEtablissements(data.etablissements || []);
    } catch (error) {
        etablissementsListe = [];
        if (!select) return;
        select.innerHTML = '';
        const option = document.createElement('option');
        option.value = '';
        option.textContent = t('etablissement_indisponible');
        select.appendChild(option);
        select.disabled = true;
    }
}

/* Établissement à associer à la Feuille de soins : la sélection de la liste,
   ou — à défaut — un nom saisi qui correspond exactement à un établissement. */
function etablissementSelectionne() {
    const select = document.getElementById('etablissement-select');
    if (select && select.value) return select.value;

    const recherche = document.getElementById('etablissement-recherche');
    const saisie = recherche ? recherche.value.trim() : '';
    if (!saisie) return '';

    const cible = normaliserEtablissement(saisie);
    const trouve = etablissementsListe.find(etablissement =>
        normaliserEtablissement(etablissement.nom) === cible
        || normaliserEtablissement(etablissement.libelle || '') === cible);

    return trouve ? String(trouve.id) : '';
}

/* Accents, casse et ponctuation sont ignorés (comme côté serveur). */
function normaliserEtablissement(texte) {
    return String(texte || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9]+/gi, ' ')
        .trim()
        .toLowerCase();
}

/* Le choix de l'établissement est obligatoire : tant qu'aucun hôpital
   n'est sélectionné, la saisie du NNI / INAM et le bouton « Vérifier »
   restent désactivés. Appelée au démarrage et à chaque changement. */
function majEtatChampIdentifiant() {
    const champ = document.getElementById('assure-identifiant');
    const bouton = document.getElementById('btn-verifier-assure');
    const avertissement = document.getElementById('assure-identifiant-avertissement');

    const choisi = Boolean(etablissementSelectionne());

    if (champ) champ.disabled = !choisi;
    if (bouton) bouton.disabled = !choisi;
    if (avertissement) {
        avertissement.hidden = choisi;
        avertissement.textContent = choisi ? '' : t('msg_etablissement_requis');
    }
}

/* Branche la recherche par nom et la liste déroulante. */
function initEtablissements() {
    const recherche = document.getElementById('etablissement-recherche');
    const select    = document.getElementById('etablissement-select');
    if (!recherche || !select) return;

    chargerEtablissements('');

    recherche.addEventListener('input', () => {
        clearTimeout(rechercheEtablissementTimer);
        rechercheEtablissementTimer = setTimeout(
            () => chargerEtablissements(recherche.value.trim()), 250);
    });

    /* Le nom choisi est recopié dans la recherche : la saisie reste consultable. */
    select.addEventListener('change', () => {
        const choisi = etablissementsListe.find(e => String(e.id) === select.value);
        if (choisi) recherche.value = choisi.nom || '';
        majEtatChampIdentifiant();
    });

    /* Le champ NNI / INAM reste verrouillé tant qu'aucun hôpital n'est choisi. */
    majEtatChampIdentifiant();
}

/* La touche Entrée dans le champ NNI/INAM lance la vérification. */
function initRechercheAssure() {
    const champ = document.getElementById('assure-identifiant');
    if (!champ) return;

    champ.addEventListener('keydown', event => {
        if (event.key === 'Enter') {
            event.preventDefault();
            verifierAssure();
        }
    });
}

/* ============================================================
   SHOW DASHBOARD
   ============================================================ */
function showDashboard() {
    const authContainer      = document.getElementById('auth-container');
    const authLangBar        = document.getElementById('auth-lang-bar');
    const dashboardContainer = document.getElementById('dashboard-container');

    authContainer.style.opacity = '0';

    setTimeout(() => {
        authContainer.style.display = 'none';
        if (authLangBar) authLangBar.style.display = 'none';

        dashboardContainer.classList.remove('hidden');
        dashboardContainer.style.opacity = '0';
        void dashboardContainer.offsetWidth;

        dashboardContainer.style.transition = 'opacity 0.4s ease';
        dashboardContainer.style.opacity    = '1';
    }, 300);
}

/* ============================================================
   DASHBOARD TAB SWITCH
   ============================================================ */
function switchDashboardTab(tabId) {
    document.querySelectorAll('.dashboard-tab').forEach(tab => tab.classList.add('hidden'));
    document.querySelectorAll('.nav-tab').forEach(btn => btn.classList.remove('active'));

    document.getElementById(tabId).classList.remove('hidden');
    document.getElementById('btn-' + tabId).classList.add('active');
}

/* ============================================================
   PROFILE DROPDOWN
   ============================================================ */
function toggleProfileDropdown() {
    document.getElementById('profileDropdown').classList.toggle('hidden');
}

/* ============================================================
   LOGOUT
   ============================================================ */
function logout() {
    // Ferme la session côté serveur (sans bloquer l'animation de déconnexion).
    apiRequest('/api/logout/', {}).catch(() => {});
    setConnectedUser('');

    document.getElementById('profileDropdown').classList.add('hidden');

    const authContainer      = document.getElementById('auth-container');
    const authLangBar        = document.getElementById('auth-lang-bar');
    const dashboardContainer = document.getElementById('dashboard-container');

    dashboardContainer.style.opacity = '0';

    setTimeout(() => {
        dashboardContainer.classList.add('hidden');
        authContainer.style.display = '';
        if (authLangBar) authLangBar.style.display = '';

        authContainer.style.opacity = '0';
        void authContainer.offsetWidth;

        authContainer.style.transition = 'opacity 0.4s ease';
        authContainer.style.opacity    = '1';

        switchAuthView('login-view');
    }, 300);
}

/* ============================================================
   CLOSE DROPDOWN ON OUTSIDE CLICK
   ============================================================ */
document.addEventListener('click', function (e) {
    const menu     = document.querySelector('.profile-menu');
    const dropdown = document.getElementById('profileDropdown');
    if (menu && dropdown && !menu.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});
