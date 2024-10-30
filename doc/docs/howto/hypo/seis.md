# hypomhによる震源決定
???+ Tip "hypomhの使い方"
    [https://wwweic.eri.u-tokyo.ac.jp/WIN/man.ja/hypomh.html](https://wwweic.eri.u-tokyo.ac.jp/WIN/man.ja/hypomh.html)

    ```bash
    hypomh stan sies final report [init]
    ```
    `report`が不要な場合は`/dev/null`とする．

## ファイルの準備
検測値ファイル`seis`, 初期震源ファイル`init`を作成する必要がある．

### seisファイルの作成
`wintools.Seis.make`を使って検測ファイルを作成する．  
基準時刻と観測点の緯度，経度，標高[m]，10文字以内の観測点コード（英数の観測点名），
P,Sの基準時刻からの秒数，P,Sそれぞれの不確かさ[s]などが必要．

#### 気象庁検測値レコードからの変換
`seisdbpy`と連携する必要がある．
必要なデータは次の通り．
- 観測点ファイル（防災科研でログインしてダウンロードする）
- 気象庁の検測値レコードファイル（新しいものは防災科研，しばらく経過したものは気象庁よりダウンロード）
- 観測点補正値（海域観測点を使う場合に必要．気象庁よりダウンロード．）

まず`seisdbpy`で気象庁のイベントレコードを読み取る．
```python
df = seisdbpy.read_jma_record(fp)
```
ここでは全てのイベントが含まれているため，
必要に応じて時刻，位置などによってイベントを絞り込むと良い．

次に`seisdbpy.jma_record2seis`メソッドでseisファイルを保存する．
このときに観測点ファイルと観測点補正値を与える．
```python
    seisdbpy.jma_record2seis(
        df, # 読み込んだ気象庁のイベントレコード
        stationfp, # 観測点情報のファイル
        stncorrectionfp = stcfp, # 観測点補正値のファイル
        pcert = pcert,
        scert = scert,
        savedir = seis_savedir,
    )
```
するとdfに含まれるイベントそれぞれに対して，
`savedir`に指定したディレクトリにseisファイルが保存される．

#### 複数のseisファイルの結合
同一イベントを異なる観測網で検測したなどの事情によってseisファイルが複数に分かれている場合，
`wintools.Seis`オブジェクトを`+`で「足す」ことで結合した`Seis`オブジェクトを作成できる．

したがって，二つのseisファイルを結合したい場合，
まずそれぞれを`wintools.read_seis`で読み込み，それらを足し合わせて一つにして保存すれば良い．
```python
seis1 = wintools.read_seis(fp1)
seis2 = wintools.read_seis(fp2)
seis = seis1 + seis2
seis.write(
    outdir = "./",
    outname = 任意の保存名,
)
```

### initファイルの作成
震源決定時の初期震源の位置とその不確かさを与えるファイル．
initファイルの使用は任意で，与えない場合は速度構造ファイル`stan`に与えられたものが用いられる．

WINによる震源決定と同一の処理にしたい場合，
初期震源の緯度と経度を初めにP波が検測された観測点の位置とする．
この処理のためのinitファイルを作成するには，
`wintools.seis2init`メソッドを使用する．
seisファイル，初期震源の深さ[km], 緯度・経度・深さ方向の不確かさ，保存ディレクトリを与える．
