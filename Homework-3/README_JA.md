# Homework-3: DOBOT ME6 ROS 2 Docker 環境

このディレクトリは、ホスト側に ROS 1 が入っている環境でも、Docker 内で ROS 2 Humble を使って DOBOT ME6/E6 の表示、MoveIt、Gazebo シミュレーション、実機接続前チェックを行うための環境です。ロボットモデルは `Dobot-Arm/DOBOT_6Axis_ROS2_V4` の公式 ROS 2 SDK を `ros2_ws/src/DOBOT_6Axis_ROS2_V4` に取り込んで使用します。

## 構成

- `docker/`: ROS 2 Humble + Gazebo + MoveIt + ros2_control 用 Dockerfile
- `compose.yaml`: GUI、ネットワーク、実機接続用の Docker Compose 設定
- `ros2_ws/src/DOBOT_6Axis_ROS2_V4`: DOBOT 公式 ROS 2 SDK。ME6/E6 の URDF、STL メッシュ、MoveIt、Gazebo、実機 TCP 連携を含む
- `ros2_ws/src/dobot_me6_description`: 授業用の近似 fallback URDF/Xacro
- `ros2_ws/src/dobot_me6_bringup`: 近似モデル用 RViz、Fake control、Gazebo 起動 launch
- `ros2_ws/src/dobot_me6_driver`: 実機 TCP 接続前チェックと安全付き dry-run 軌道ブリッジ
- `ros2_ws/src/dobot_me6_examples`: JointTrajectory の送信例
- `UPSTREAM_DOBOT_6AXIS_ROS2_V4.md`: 公式 SDK の取り込み元と commit

## 動作環境

この環境は以下の構成を想定しています。

| 項目 | 推奨/使用バージョン |
| --- | --- |
| ホスト OS | Ubuntu 22.04 LTS で確認 |
| Docker Engine | 20.10.17 以降 |
| Docker Compose | Docker Compose plugin v2.6.0 以降 |
| コンテナ OS | Ubuntu 22.04 系 |
| ROS 2 | Humble Hawksbill |
| Docker base image | `osrf/ros:humble-desktop` |
| Gazebo | ROS 2 Humble apt パッケージで提供される Gazebo Classic |
| GUI | X11 |
| CPU/メモリ | x86_64、8 GB RAM 以上推奨 |
| ディスク容量 | Docker image と workspace 用に 10 GB 以上推奨 |
| 実機接続 | DOBOT ME6 と同一ネットワークに接続できる有線 LAN 推奨 |

Docker の導入は Ubuntu 22.04 上で Docker 公式 apt repository を登録する方法を想定しています。手元環境では Qiita の「Ubuntu 22.04にdockerをインストールする」を参考にしました。

ホスト側のバージョン確認:

```bash
docker --version
docker compose version
uname -m
lsb_release -a
```

コンテナ内の ROS 2 確認:

```bash
make shell
ros2 --version
printenv ROS_DISTRO
```

`printenv ROS_DISTRO` が `humble` を返せば、このプロジェクトが想定する ROS 2 環境です。

## 環境構築

ホスト側には Docker と Docker Compose plugin が必要です。ROS 2 は Docker コンテナ内だけで使うため、ホスト側に ROS 1 が入っていても問題ありません。GUI を使う場合は X11 が使える Linux デスクトップを想定しています。

### 1. Docker をインストール

Docker 未導入の Ubuntu 22.04 では、Docker 公式 apt repository から Docker Engine と Compose plugin をインストールします。

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

インストール後、Docker daemon が起動していることを確認します。

```bash
sudo systemctl status docker
sudo docker run hello-world
docker compose version
```

`sudo docker run hello-world` が成功すれば Docker のインストール自体は完了です。以降の `make build` / `make ws` を `sudo` なしで実行したい場合は、次の手順でユーザ権限を設定します。

### 2. Docker の利用権限を確認

まず Docker daemon に現在のユーザで接続できるか確認します。

```bash
docker ps
```

`permission denied while trying to connect to the docker API` が出る場合は、現在のユーザを `docker` グループに追加します。

```bash
sudo usermod -aG docker $USER
```

注意: `docker` グループに入ったユーザは Docker daemon 経由で root 相当の操作が可能です。共用PCでは管理方針を確認してください。

このコマンドは一度だけ実行すれば十分です。`.bashrc` には書かないでください。グループ変更を反映するには、Ubuntu から一度ログアウトして再ログインするか、現在の端末だけ反映する場合は次を実行します。

```bash
newgrp docker
docker ps
```

### 3. Homework-3 に移動

この README がある `Homework-3` ディレクトリに移動します。すでに `~/Expressive_Robot_Control/Homework-3` にいる場合は、追加で `cd Homework-3` しないでください。

```bash
cd ~/Expressive_Robot_Control/Homework-3
```

### 4. GUI 表示を許可

RViz/Gazebo を Docker コンテナから表示するため、X11 のローカル接続を許可します。

```bash
xhost +local:docker
```

作業後に戻す場合は次を実行します。

```bash
xhost -local:docker
```

### 5. Docker イメージをビルド

ROS 2 Humble、Gazebo、MoveIt、ros2_control、DOBOT 公式 SDK のビルドに必要な依存関係を含む Docker イメージを作成します。

```bash
make build
```

### 6. ROS 2 ワークスペースをビルド

`rosdep` で依存関係を解決し、`colcon` で ME6 関連パッケージをビルドします。

```bash
make ws
```

ビルド済みコンテナに入って手動で確認したい場合は次を使います。

```bash
make shell
source install/setup.bash
ros2 pkg list | grep -E 'dobot|me6|cra_description'
```

注: 公式 `me6_moveit/package.xml` には `warehouse_ros_mongo` が含まれていますが、ROS 2 Humble の apt では `ros-humble-warehouse-ros-mongo` が提供されないため、`make ws` では rosdep 解決から除外しています。通常の RViz、Gazebo、MoveIt デモには不要です。

## RViz でモデルを確認

公式 ME6 モデルを RViz で表示します。

```bash
make rviz
```

別端末でコンテナに入り、サンプル姿勢を送れます。

```bash
cd Homework-3
make shell
source install/setup.bash
ros2 run dobot_me6_examples send_joint_goal --target ready
```

## Fake control で軌道検証

実機を動かさず、ローカル fallback モデルの `joint_trajectory_controller` まで含めて ROS 2 側の軌道送信を確認します。

```bash
make fake
```

別端末:

```bash
make shell
source install/setup.bash
ros2 run dobot_me6_examples send_joint_goal --target home
```

## EE 軌道スクリプト

`make fake` で `me6_arm_controller` を起動した状態で、別端末からエンドエフェクタ位置軌道を個別に実行できます。各スクリプトは現在姿勢を起点に、位置タスク用の簡易差分IKで `FollowJointTrajectory` を送信します。

```bash
make shell
source install/setup.bash
```

円軌道:

```bash
ros2 run dobot_me6_examples ee_circle --duration 12 --radius 0.055 --plane xy
```

8の字軌道:

```bash
ros2 run dobot_me6_examples ee_figure8 --duration 12 --width 0.10 --height 0.055 --plane xy
```

直線往復:

```bash
ros2 run dobot_me6_examples ee_line --duration 10 --length 0.12 --axis x
```

キーボード操縦:

```bash
ros2 run dobot_me6_examples ee_keyboard
```

キー割り当ては `w/s: +X/-X`, `a/d: +Y/-Y`, `r/f: +Z/-Z`, `q: quit` です。実機接続時は使わず、まず `make fake` で動作確認してください。

## Gazebo シミュレーション

公式 SDK の ME6 モデルを Gazebo に spawn します。

```bash
make sim
```

MoveIt の仮想デモは次で起動します。

```bash
make moveit
```

通常は公式 SDK 内の `cra_description/urdf/me6_robot.xacro` と `me6_moveit` を優先してください。`dobot_me6_description` はネットワークや upstream 依存なしで最低限の ROS 2 制御を試す fallback です。

## 実機検証

まずロボットを動かさず通信だけ確認します。

```bash
export DOBOT_ME6_IP=192.168.5.1
make real-check
```

軌道ブリッジは初期状態では dry-run です。

```bash
make shell
source install/setup.bash
ros2 launch dobot_me6_driver real_validation.launch.py robot_ip:=$DOBOT_ME6_IP dry_run:=true
```

公式 SDK の TCP bringup を使う場合:

```bash
make real
```

実機へ送信する場合のみ `dry_run:=false` にします。非常停止、可動範囲、周囲の安全、速度制限、メーカー純正ソフトでの原点復帰を確認してから実行してください。

```bash
ros2 launch dobot_me6_driver real_validation.launch.py robot_ip:=$DOBOT_ME6_IP dry_run:=false speed_ratio:=10.0
```

別端末から:

```bash
ros2 run dobot_me6_examples send_joint_goal --target ready --duration 5.0
```

注意: `dobot_me6_driver` の TCP コマンドは DOBOT CR/CRA 系 Dashboard/Motion API の一般的な形式をベースにした雛形です。ME6 のファームウェアでコマンド名、ポート、単位、軸順が異なる場合は `dobot_dashboard_client.py` を実機マニュアルに合わせて修正してください。

## ROS 1 との分離

ホスト側の ROS 1 は使いません。ROS 2 の環境変数、Python パッケージ、Gazebo 関連パッケージは Docker イメージ内に閉じています。ホスト側で必要なのは Docker、GUI 表示用 X11、実機 LAN 接続だけです。

## 参考

- Docker Docs: Install Docker Engine on Ubuntu: https://docs.docker.com/engine/install/ubuntu/
- Docker Docs: Linux post-installation steps for Docker Engine: https://docs.docker.com/engine/install/linux-postinstall/
- Qiita: Ubuntu 22.04にdockerをインストールする: https://qiita.com/yoshiyasu1111/items/17d9d928ceebb1f1d26d
