"""マイページ収集の純関数テスト。Chromeのファイルには触れない。

実行: python3 -m unittest discover apps/job-hunt-board/tests
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))
import collect_mypages as cm  # noqa: E402


class AtsTest(unittest.TestCase):
    def test_axol_zw(self):
        got = cm.ats_of("axol.jp", "/zw/s/kddi_28/mypage/login")
        self.assertEqual(got["key"], "axol:kddi_28")
        self.assertEqual(got["login_url"], "https://axol.jp/zw/s/kddi_28/mypage/login")
        self.assertEqual(got["home_url"], "https://axol.jp/zw/s/kddi_28/mypage/top")

    def test_axol_job(self):
        got = cm.ats_of("job.axol.jp", "/ff/c/pwc/mypage/top")
        self.assertEqual(got["key"], "axol-ff:pwc")

    def test_i_webs(self):
        got = cm.ats_of("mypage.3030.i-webs.jp", "/pwc_newgrads28/applicant/top/index/")
        self.assertEqual(got["key"], "i-webs:pwc_newgrads28")
        self.assertEqual(got["login_url"], "https://mypage.3030.i-webs.jp/pwc_newgrads28/")

    def test_i_web_jpn(self):
        got = cm.ats_of("mypage.1050.i-web.jpn.com", "/scsk2028/")
        self.assertEqual(got["key"], "i-web-jpn:scsk2028")

    def test_snar(self):
        got = cm.ats_of("softbank-recruit.snar.jp", "/login.aspx")
        self.assertEqual(got["key"], "snar:softbank-recruit")

    def test_saiyo(self):
        got = cm.ats_of("orix-group.saiyo.jp", "/2028/")
        self.assertEqual(got["key"], "saiyo:orix-group")

    def test_mufg_smbc(self):
        self.assertEqual(cm.ats_of("www.mypage.bk.mufg.jp", "/mufgbank2028/")["key"],
                         "mufg-bk:mufgbank2028")
        self.assertEqual(cm.ats_of("mypage.smbc-recruitment.jp", "/2028/")["key"], "smbc:2028")

    def test_talent_p_requires_token(self):
        self.assertIsNone(cm.ats_of("recruit.talent-p.net", "/Auth/Login/"))
        got = cm.ats_of("recruit.talent-p.net", "/Auth/Login/74249f958c81423d89315474c7747990")
        self.assertEqual(got["key"], "talent-p:74249f95")

    def test_unrelated_host(self):
        self.assertIsNone(cm.ats_of("www.openwork.jp", "/mypage"))
        self.assertIsNone(cm.ats_of("www.google.com", "/url"))


class NameTest(unittest.TestCase):
    def test_strips_noise(self):
        self.assertEqual(cm.clean_name("株式会社シグマクシス　2028年度　マイページ"), "シグマクシス")
        self.assertEqual(cm.clean_name("野村総合研究所（ＮＲＩ）2028年新卒向けマイページ"),
                         "野村総合研究所(NRI)")
        self.assertEqual(cm.clean_name("【新卒】28卒マイページ"), "")
        self.assertEqual(cm.clean_name("Sansan株式会社｜新卒採用"), "Sansan")

    def test_strip_corp_keeps_holidings(self):
        self.assertEqual(cm.strip_corp("シンプレクス・ホールディングス"), "シンプレクス・ホールディングス")


if __name__ == "__main__":
    unittest.main()
