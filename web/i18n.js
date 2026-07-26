const I18n = {
    language: 'en',
    packs: {
        en: ['Support Lending Pro Freeware','If you appreciate this software, you can buy me a coffee.','Suggested minimum donation: €5.','Installation ID','Later','Buy me a coffee'],
        fr: ['Soutenir Lending Pro Freeware',"Si vous appréciez mon logiciel, vous pouvez m'offrir un café.",'Don minimum conseillé : 5 €.','Identifiant de cette installation','Plus tard','Offrir un café'],
        es: ['Apoyar Lending Pro Freeware','Si te gusta este programa, puedes invitarme a un café.','Donación mínima sugerida: 5 €.','ID de instalación','Más tarde','Invitar a un café'],
        de: ['Lending Pro Freeware unterstützen','Wenn Ihnen die Software gefällt, können Sie mir einen Kaffee spendieren.','Empfohlene Mindestspende: 5 €.','Installations-ID','Später','Kaffee spendieren'],
        it: ['Sostieni Lending Pro Freeware','Se apprezzi il software, puoi offrirmi un caffè.','Donazione minima consigliata: 5 €.','ID installazione','Più tardi','Offri un caffè'],
        pt: ['Apoiar Lending Pro Freeware','Se gosta do software, pode oferecer-me um café.','Doação mínima sugerida: 5 €.','ID da instalação','Mais tarde','Oferecer um café'],
        nl: ['Lending Pro Freeware steunen','Als u de software waardeert, kunt u mij op koffie trakteren.','Aanbevolen minimale donatie: € 5.','Installatie-ID','Later','Koffie aanbieden'],
        fil: ['Suportahan ang Lending Pro Freeware','Kung gusto mo ang software, maaari mo akong ilibre ng kape.','Iminungkahing minimum na donasyon: €5.','Installation ID','Mamaya','Maglibre ng kape'],
        zh: ['支持 Lending Pro Freeware','如果您喜欢这个软件，可以请我喝杯咖啡。','建议最低捐赠：5 欧元。','安装标识','稍后','请喝咖啡'],
        ja: ['Lending Pro Freeware を支援','このソフトウェアが気に入ったら、コーヒーをご支援いただけます。','推奨最低寄付額：5ユーロ。','インストールID','後で','コーヒーを贈る'],
        ko: ['Lending Pro Freeware 후원','이 소프트웨어가 마음에 드시면 커피 한 잔을 후원해 주세요.','권장 최소 후원금: 5유로.','설치 ID','나중에','커피 후원'],
        ar: ['دعم Lending Pro Freeware','إذا أعجبك البرنامج، يمكنك دعوتي إلى فنجان قهوة.','الحد الأدنى المقترح للتبرع: 5 يورو.','معرّف التثبيت','لاحقاً','قدّم قهوة'],
        hi: ['Lending Pro Freeware का समर्थन करें','यदि आपको यह सॉफ्टवेयर पसंद है, तो आप मुझे कॉफी पिला सकते हैं।','सुझाया गया न्यूनतम दान: €5।','इंस्टॉलेशन आईडी','बाद में','कॉफी दें'],
        th: ['สนับสนุน Lending Pro Freeware','หากคุณชอบซอฟต์แวร์นี้ คุณสามารถเลี้ยงกาแฟฉันได้','เงินบริจาคขั้นต่ำที่แนะนำ: €5','รหัสการติดตั้ง','ภายหลัง','เลี้ยงกาแฟ'],
        ms: ['Sokong Lending Pro Freeware','Jika anda menghargai perisian ini, anda boleh belanja saya kopi.','Derma minimum dicadangkan: €5.','ID pemasangan','Nanti','Belanja kopi'],
        id: ['Dukung Lending Pro Freeware','Jika Anda menyukai perangkat lunak ini, Anda dapat mentraktir saya kopi.','Donasi minimum yang disarankan: €5.','ID instalasi','Nanti','Traktir kopi'],
        vi: ['Ủng hộ Lending Pro Freeware','Nếu bạn thích phần mềm này, bạn có thể mời tôi một ly cà phê.','Mức ủng hộ tối thiểu đề xuất: 5 €.','Mã cài đặt','Để sau','Mời cà phê']
    },
    keys: ['title','message','minimum','installation','later','coffee'],
    extra: {
        en: {
            copy: 'Copy installation ID',
            instruction: 'Copy this ID into your Ko-fi message to associate the donation with this Mac.',
            reminder: 'The reminder stays active until an associated payment is verified.',
            support: 'Support the software',
            supportDescription: 'Help keep Lending Pro Freeware available for free.'
        },
        fr: {
            copy: "Copier l'identifiant",
            instruction: "Copiez cet identifiant dans le message Ko-fi pour associer le don à ce Mac.",
            reminder: "Le rappel reste actif tant qu'aucun paiement associé n'a été vérifié.",
            support: 'Soutenir le logiciel',
            supportDescription: 'Aidez à maintenir Lending Pro Freeware disponible gratuitement.'
        }
    },
    setLanguage(code) {
        const value = String(code || 'en').split('-')[0].toLowerCase();
        this.language = this.packs[value] ? value : 'en';
        document.documentElement.lang = this.language;
        document.documentElement.dir = this.language === 'ar' ? 'rtl' : 'ltr';
    },
    t(key) {
        const index = this.keys.indexOf(key);
        return index < 0 ? key : this.packs[this.language][index];
    },
    x(key) {
        return (this.extra[this.language] || this.extra.en)[key] || this.extra.en[key];
    }
};
