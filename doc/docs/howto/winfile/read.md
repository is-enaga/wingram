## WINファイルの読み込み

### 概要
`wintools.read`関数を使う．
引数にはWINファイルのパスを与える．
戻り値は`WIN`クラス, 単数チャネルの場合は`WIN1ch`クラスである．

- `fp`引数にファイル名を文字列（複数あればそのリスト）で与える．
- もしもファイル名に末尾に「.ch」で与えたファイルが存在すれば，
自動的にそのチャネルテーブルも読み込む．
- `chtable`引数で明示的にチャンネルテーブルのファイル名を与えると，その情報を読み込んで，`WIN.chtable`に格納する．
- `sort`引数（デフォルトは`True`）によって，出力される`WIN`クラスをチャンネル番号順に並べ替えるかどうかを切り替えられる．

???+ example 
    ```python
    import wintools
    fp = "991109.064607"

    dat = wintools.read(
        fp,
    )
    ```

### チャネルテーブル情報の付加
チャネルテーブルがあるなら，引数に与えることを推奨する．

`chtable`にチャネルテーブルのファイルパスを与えることで，
観測点名，成分名，振幅倍率の情報もデータに保持できる．
`encoding`でチャネルテーブルの文字コードを指定する．
`apply_chtbl`を`True`（デフォルトは`False`）にすると，チャネルテーブルの値を使って振幅を物理量へ変換したデータを出力する．

???+ example 
    ```python
    import wintools

    fp = "991109.064607"
    chtbl = "991109.064607.ch

    dat = wintools.read(
        fp,
        chtable = chtbl,
        encoding = "utf-8",
        apply_calib=True,
    )
    ```


### 複数WINファイルの読み込み
`wintools.read`関数で，fp引数にリストを与える．
このリストは，時間方向に連続したWINファイルのパスである必要がある．

チャネルテーブルやsortの設定は，単体ファイルの時と同様．

さらに，fpに候補のファイルを与えた上で，
`targettime`, `beforesec`, `aftersec`を指定すると，
候補ファイルの中から指定した時刻範囲のデータを抽出して読み込むことができる．

???+ example
    ```python
    import wintools
    import glob
    import datetime

    tar = sorted(glob.glob("./data/win/*.*"))
    chtbl = "./data/chtbl.tbl"

    dat = wintools.read(
        tar,
        chtbl,
        targettime  = datetime.datetime(2023,10,29,11,25,30),
        beforesec = 5,
        aftersec = 60,
        # filenameformat = "%y%m%d%H.%M",
        )
    ```

