# Rustyvibes

キーを押すたびに打鍵音を再生する、Macにインストールしたツールです。

## 起動と停止

[起動ファイル](../../Applications/Rustyvibes.command)をダブルクリックします。
音源はNK Cream、音量は30%です。開いたターミナルでControl + Cを押すと停止します。
自動起動は設定していません。

ターミナルから直接起動する場合は次を実行します。

```sh
~/.cargo/bin/rustyvibes "$HOME/Library/Application Support/Rustyvibes/nk-cream" -v 30
```

`-v 30`の数字を0〜100で指定すると音量が変わります。
同時に複数起動すると音が重なるため、音量変更時は先に停止します。

## インストール内容

- HomebrewでRustを導入しました。
- crates.ioからRustyvibes 1.0.9をインストールしました。
- [音源設定](<../../Library/Application Support/Rustyvibes/nk-cream/config.json>)は、MechvibesのNK Creamを使用しています。
- 音が未指定だったキーの設定をa.wavに補完しました。

ソースは[公式リポジトリ](https://github.com/kunalbagaria/rustyvibes)、音源は[MechvibesのNK Cream](https://github.com/hainguyents13/mechvibes/tree/main/src/audio/nk-cream)です。

## 音が出ないとき

Macの「システム設定 → プライバシーとセキュリティ → 入力監視」で、起動元のターミナルを許可し、起動し直します。必要に応じてターミナル自体も終了して開き直します。

制限された実行環境ではEventTapErrorで停止しました。通常の環境から起動すると、音源を読み込み、入力待ちの状態を維持しました。

## 確認したこと

バージョン表示、音源34ファイルの読み込み、対応77キーの割り当て、通常環境での起動を確認しました。実際に打鍵音が聞こえるかは本人の確認待ちです。
