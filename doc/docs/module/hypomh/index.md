# hypomh関連
hypomhのコマンドに関連するファイルを扱うモジュール．

???+ Tip "hypomhの使い方"
    [https://wwweic.eri.u-tokyo.ac.jp/WIN/man.ja/hypomh.html](https://wwweic.eri.u-tokyo.ac.jp/WIN/man.ja/hypomh.html)

    ```bash
    hypomh stan seis final report [init]
    ```
    `report`が不要な場合は`/dev/null`とする．

## 仕様
ライブラリでサポートしている機能は以下の表のとおり．

| ファイル | 概要         | 作成                         | 読み込み                      |
| -------- | ------------ | :--------------------------- | :---------------------------- |
| `stan`   | 速度構造     | :material-check: `mkstan`    | :material-close:              |
| `seis`   | 検測値       | :material-check: `Seis.make` | :material-check: `Seis.read`  |
| `final`  | 震源決定結果 | :material-close:             | :material-check: `Final.read` |
| `init`   | 初期震源     | :material-check: `mkinit`    | :material-close:              |
