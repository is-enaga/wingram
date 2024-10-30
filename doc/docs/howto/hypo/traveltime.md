# hypomhによる走時計算
!!! Note "hypomh公式マニュアル"
    [https://wwweic.eri.u-tokyo.ac.jp/WIN/man.ja/hypomh.html](https://wwweic.eri.u-tokyo.ac.jp/WIN/man.ja/hypomh.html)
    > hypomhには「走時計算モード」があります。 seis と init を次の形式にすることにより、 与えた速度構造と震源要素から 計算される各観測点の理論走時(PとSの到着時刻)を final に出力することができます。  
    >
    >seis  
    PとSの到着時刻データをすべてゼロにしてください。  
    init  
    ３行目として震源要素(年、月、日、時、分、秒、緯度、経度、深さ、M )を 適当に空白で区切って書いてください(" 93 7 22 12 6 2.162 34.76181 140.09901 60.004 2.0"など) 。
 
hypomhの走時計算モードを使用するためには，
あらかじめ指定されたseisファイルとinitファイルを作成する必要がある．

### 1. 走時計算用seisファイルの作成

### 2. 走時計算用initファイルの作成