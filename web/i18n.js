const I18n = {
    language: 'en',
    packs: {
        en: ['Support Lending Pro Freeware','If you appreciate this software, you can buy me a coffee.','Suggested minimum donation: €5.','Later','Buy me a coffee','I made a donation','This reminder appears at most once a week.','Thank you. The next reminder will be in about three months.','Thank you for your support.'],
        fr: ['Soutenir Lending Pro Freeware',"Si vous appréciez mon logiciel, vous pouvez m'offrir un café.",'Don minimum conseillé : 5 €.','Plus tard','Offrir un café',"J'ai fait un don",'Ce rappel apparaît au maximum une fois par semaine.','Merci. Le prochain rappel apparaîtra dans environ trois mois.','Merci pour votre soutien.'],
        es: ['Apoyar Lending Pro Freeware','Si te gusta este programa, puedes invitarme a un café.','Donación mínima sugerida: 5 €.','Más tarde','Invitar a un café','He hecho una donación','Este recordatorio aparece como máximo una vez por semana.','Gracias. El próximo recordatorio aparecerá en unos tres meses.','Gracias por tu apoyo.'],
        de: ['Lending Pro Freeware unterstützen','Wenn Ihnen die Software gefällt, können Sie mir einen Kaffee spendieren.','Empfohlene Mindestspende: 5 €.','Später','Kaffee spendieren','Ich habe gespendet','Diese Erinnerung erscheint höchstens einmal pro Woche.','Danke. Die nächste Erinnerung erscheint in etwa drei Monaten.','Vielen Dank für Ihre Unterstützung.'],
        it: ['Sostieni Lending Pro Freeware','Se apprezzi il software, puoi offrirmi un caffè.','Donazione minima consigliata: 5 €.','Più tardi','Offri un caffè','Ho fatto una donazione','Questo promemoria appare al massimo una volta alla settimana.','Grazie. Il prossimo promemoria apparirà tra circa tre mesi.','Grazie per il tuo sostegno.'],
        pt: ['Apoiar Lending Pro Freeware','Se gosta do software, pode oferecer-me um café.','Doação mínima sugerida: 5 €.','Mais tarde','Oferecer um café','Fiz uma doação','Este lembrete aparece no máximo uma vez por semana.','Obrigado. O próximo lembrete aparecerá dentro de cerca de três meses.','Obrigado pelo seu apoio.'],
        nl: ['Lending Pro Freeware steunen','Als u de software waardeert, kunt u mij op koffie trakteren.','Aanbevolen minimale donatie: € 5.','Later','Koffie aanbieden','Ik heb gedoneerd','Deze herinnering verschijnt maximaal één keer per week.','Bedankt. De volgende herinnering verschijnt over ongeveer drie maanden.','Bedankt voor uw steun.'],
        fil: ['Suportahan ang Lending Pro Freeware','Kung gusto mo ang software, maaari mo akong ilibre ng kape.','Iminungkahing minimum na donasyon: €5.','Mamaya','Maglibre ng kape','Nagbigay ako ng donasyon','Lumalabas ang paalalang ito nang hindi hihigit sa isang beses kada linggo.','Salamat. Lalabas ang susunod na paalala pagkalipas ng humigit-kumulang tatlong buwan.','Salamat sa iyong suporta.'],
        zh: ['支持 Lending Pro Freeware','如果您喜欢这个软件，可以请我喝杯咖啡。','建议最低捐赠：5 欧元。','稍后','请喝咖啡','我已捐赠','此提醒每周最多显示一次。','感谢支持。下次提醒将在大约三个月后显示。','感谢您的支持。'],
        ja: ['Lending Pro Freeware を支援','このソフトウェアが気に入ったら、コーヒーをご支援いただけます。','推奨最低寄付額：5ユーロ。','後で','コーヒーを贈る','寄付しました','この通知は週に1回まで表示されます。','ありがとうございます。次回の通知は約3か月後に表示されます。','ご支援ありがとうございます。'],
        ko: ['Lending Pro Freeware 후원','이 소프트웨어가 마음에 드시면 커피 한 잔을 후원해 주세요.','권장 최소 후원금: 5유로.','나중에','커피 후원','후원했습니다','이 알림은 일주일에 한 번만 표시됩니다.','감사합니다. 다음 알림은 약 3개월 후에 표시됩니다.','후원해 주셔서 감사합니다.'],
        ar: ['دعم Lending Pro Freeware','إذا أعجبك البرنامج، يمكنك دعوتي إلى فنجان قهوة.','الحد الأدنى المقترح للتبرع: 5 يورو.','لاحقاً','قدّم قهوة','لقد تبرعت','يظهر هذا التذكير مرة واحدة أسبوعياً كحد أقصى.','شكراً لك. سيظهر التذكير التالي بعد نحو ثلاثة أشهر.','شكراً لدعمك.'],
        hi: ['Lending Pro Freeware का समर्थन करें','यदि आपको यह सॉफ्टवेयर पसंद है, तो आप मुझे कॉफी पिला सकते हैं।','सुझाया गया न्यूनतम दान: €5।','बाद में','कॉफी दें','मैंने दान किया है','यह रिमाइंडर सप्ताह में अधिकतम एक बार दिखाई देता है।','धन्यवाद। अगला रिमाइंडर लगभग तीन महीने बाद दिखाई देगा।','आपके समर्थन के लिए धन्यवाद।'],
        th: ['สนับสนุน Lending Pro Freeware','หากคุณชอบซอฟต์แวร์นี้ คุณสามารถเลี้ยงกาแฟฉันได้','เงินบริจาคขั้นต่ำที่แนะนำ: €5','ภายหลัง','เลี้ยงกาแฟ','ฉันบริจาคแล้ว','การแจ้งเตือนนี้จะแสดงไม่เกินสัปดาห์ละครั้ง','ขอบคุณ การแจ้งเตือนครั้งถัดไปจะแสดงในอีกประมาณสามเดือน','ขอบคุณสำหรับการสนับสนุน'],
        ms: ['Sokong Lending Pro Freeware','Jika anda menghargai perisian ini, anda boleh belanja saya kopi.','Derma minimum dicadangkan: €5.','Nanti','Belanja kopi','Saya telah menderma','Peringatan ini muncul paling banyak sekali seminggu.','Terima kasih. Peringatan seterusnya akan muncul dalam kira-kira tiga bulan.','Terima kasih atas sokongan anda.'],
        id: ['Dukung Lending Pro Freeware','Jika Anda menyukai perangkat lunak ini, Anda dapat mentraktir saya kopi.','Donasi minimum yang disarankan: €5.','Nanti','Traktir kopi','Saya telah berdonasi','Pengingat ini muncul paling banyak sekali seminggu.','Terima kasih. Pengingat berikutnya akan muncul sekitar tiga bulan lagi.','Terima kasih atas dukungan Anda.'],
        vi: ['Ủng hộ Lending Pro Freeware','Nếu bạn thích phần mềm này, bạn có thể mời tôi một ly cà phê.','Mức ủng hộ tối thiểu đề xuất: 5 €.','Để sau','Mời cà phê','Tôi đã ủng hộ','Lời nhắc này xuất hiện tối đa một lần mỗi tuần.','Cảm ơn bạn. Lời nhắc tiếp theo sẽ xuất hiện sau khoảng ba tháng.','Cảm ơn sự ủng hộ của bạn.']
    },
    keys: ['title','message','minimum','later','coffee','donated','weekly','quarterly','thanks'],
    extra: {
        en: {
            support: 'Support the software',
            supportDescription: 'Help keep Lending Pro Freeware available for free.'
        },
        fr: {
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
