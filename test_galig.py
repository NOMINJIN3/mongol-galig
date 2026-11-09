"""
Тест + нарийвчлал хэмжигч.
Ажиллуулах:  python test_galig.py
"""

from galig import to_cyrillic

# (латин, зөв кирилл) хос. Энэ жагсаалтыг томруулах нь дараагийн алхам.
PAIRS = [
    ("Ugui ee", "Үгүй ээ"),
    ("uur yu hiij boloh uu", "өөр юу хийж болох уу"),
    ("Mongoliin hamgiin tom", "Монголын хамгийн том"),
    ("herhen oroltsoh ve", "хэрхэн оролцох вэ"),
    ("hugjuulelt ruu chiglesen", "хөгжүүлэлт рүү чиглэсэн"),
    ("neelttei ehiin platform", "нээлттэй эхийн платформ"),
    ("uunees uur", "үүнээс өөр"),
    ("baigaa yu", "байгаа юу"),
    ("Dadlaga hiij ajillah", "Дадлага хийж ажиллах"),
    ("sain baina uu", "сайн байна уу"),
    ("bi surguulid yavna", "би сургуульд явна"),
    ("margaash uulzay", "маргааш уулзъя"),
    # о/ө, у/ү ялгах шалгалт
    ("mongol zuragt", "монгол зурагт"),
    ("hudulguunjuuleltiin", "хөдөлгөөнжүүлэлтийн"),
    ("Luvsanbaldanbayandorj", "Лувсанбалданбаяндорж"),
    ("muruusul moroosol", "мөрөөсөл мөрөөсөл"),
    ("hool ohin hun nom tuuh", "хоол охин хүн ном түүх"),
    ("ugluu udur hurgen orchuulga", "өглөө өдөр хүргэн орчуулга"),
    ("Ene nom sonirholtoi bna uu", "Энэ ном сонирхолтой байна уу"),
]


def evaluate():
    word_total = word_ok = sent_ok = 0
    for lat, gold in PAIRS:
        pred = to_cyrillic(lat)
        if pred == gold:
            sent_ok += 1
        else:
            print(f"  БУРУУ: {lat!r}\n    гарсан: {pred!r}\n    зөв:    {gold!r}")
        for p, g in zip(pred.split(), gold.split()):
            word_total += 1
            word_ok += p == g
    print(f"\nӨгүүлбэр: {sent_ok}/{len(PAIRS)}  "
          f"Үг: {word_ok}/{word_total} ({100 * word_ok / word_total:.1f}%)")


if __name__ == "__main__":
    evaluate()
