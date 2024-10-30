# 速度構造ファイルの処理
!!! Note "公式マニュアル"
    [https://wwweic.eri.u-tokyo.ac.jp/WIN/man.ja/win.html](https://wwweic.eri.u-tokyo.ac.jp/WIN/man.ja/win.html)

!!! Note "主な仕様"
    速度構造の層の数は約20が上限．  
    指定できるのは各層の厚さと層境界におけるVp.
    各層の速度は線形補完される．  
    Vsを個別に設定することはできず，
    \(V_s=V_p / \sqrt3 \)
    の関係と定められている．

## 速度構造ファイルの作成
