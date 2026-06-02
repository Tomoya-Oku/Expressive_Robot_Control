"""
Build a ~2-minute narrated summary video (MP4) of the Homework-2 analysis.

Usage:  python3 make_video.py [en|ja]     (default: en)

Pipeline (all local, no cloud):
  1. render image-heavy slides (1280x720, white background) from figs/ and
     outputs/, with a short caption on each,
  2. synthesise narration per slide with macOS `say`
     (en -> Samantha, female US; ja -> Kyoko, female JP),
  3. mux each slide with its narration and concatenate into the MP4.

Slide duration is driven by its narration length, so audio and video stay in
sync. A quick measure-then-rescale pass sets the speaking rate so the whole
video lands at ~1:54 (inside the 1:50-2:00 target), for any language.
"""

import os
import sys
import shutil
import subprocess
import wave
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio_ffmpeg

HERE = os.path.dirname(__file__)
ROOT = os.path.normpath(os.path.join(HERE, ".."))
FIGS = os.path.join(ROOT, "figs")
OUT = os.path.join(ROOT, "outputs")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
PAD = 0.38            # trailing silence per slide (s)
T_FINAL = 114.0       # target total length (s) -> 1:54
W, H = 1280, 720

# Japanese caption font (system fonts on macOS).
plt.rcParams["font.sans-serif"] = [
    "Hiragino Maru Gothic Pro", "Hiragino Sans", "YuGothic",
    "AppleGothic", "DejaVu Sans",
]


def _img(name, folder=FIGS):
    return os.path.join(folder, name)


# Image is shared across languages; only caption/bullets/text change.
IMAGES = [
    None,
    None,
    _img("overview.jpg"),
    _img("pca.jpg"),
    _img("knn.jpg"),
    _img("random_forest.jpg"),
    _img("logistic_regression.jpg"),
    _img("mlp.jpg"),
    _img("autoencoder.jpg"),
    None,
    _img("summary_scores.png", OUT),
    _img("cm_a.png", OUT),
    _img("expert_feature_importance.png", OUT),
    _img("pca_scatter.png", OUT),
    None,
]

EN = dict(
    voice="Samantha", base_rate=195, rate_lo=165, rate_hi=215,
    out="summary_video.mp4",
    slides=[
        dict(caption="Emotion from Expressive Gait",
             bullets=["Homework-2", "Classifying emotion from how people walk",
                      "College de France expressive gait database"],
             text="How do emotions show up in the way we walk? In this project we "
                  "classify the emotion expressed in a person's gait, using motion "
                  "capture data from the College de France expressive gait database."),
        dict(caption="The data",
             bullets=["41 reflective markers, 3D, 30 fps",
                      "4 actors x 4 emotions x ~5 trials = 81 walks",
                      "Emotions: anger, joy, neutral, sad"],
             text="Each walk is recorded with forty-one body markers in three "
                  "dimensions. We have four actors, each performing anger, joy, "
                  "neutral and sadness, for eighty-one walking trials in total."),
        dict(caption="Two philosophies, compared fairly",
             text="We compare two ways of building features. Expert features: "
                  "twenty-five hand-made numbers from biomechanics. And a pure "
                  "black box: the raw marker trajectories, almost eight thousand numbers."),
        dict(caption="PCA",
             text="On the raw data we use PCA to keep only the twenty directions of "
                  "largest variation, shrinking the dimension and the noise."),
        dict(caption="k-Nearest Neighbors",
             text="A simple classifier then votes among the five nearest walks."),
        dict(caption="Random Forest",
             text="On the expert features we use a random forest: hundreds of "
                  "decision trees that vote together."),
        dict(caption="Logistic Regression",
             text="We also use logistic regression, a simple linear model that turns "
                  "features into class probabilities."),
        dict(caption="Neural Network",
             text="As a black box, a neural network learns directly from the raw "
                  "markers, with no biomechanical knowledge added."),
        dict(caption="Autoencoder",
             text="And an autoencoder compresses the raw data into sixteen learned "
                  "numbers, without ever seeing the labels."),
        dict(caption="Honest evaluation",
             bullets=["Leave-One-Subject-Out cross-validation",
                      "Train on 3 actors, test on the 4th",
                      "Measures emotion, not who is walking"],
             text="To evaluate honestly we use leave-one-subject-out: we train on "
                  "three actors and test on the fourth, so the model must recognise "
                  "the emotion, not the person."),
        dict(caption="Results",
             text="And the winner is clear. Expert features with a random forest "
                  "reach ninety-one percent accuracy. The pure black-box neural net "
                  "only reaches forty, barely above chance."),
        dict(caption="Best model: confusion matrix",
             text="Looking closer, sadness is almost perfectly recognised. The "
                  "confusions happen between anger and joy, which are both energetic, "
                  "high-arousal emotions."),
        dict(caption="What matters",
             text="The most useful features are motion energy, trunk lean, elbow "
                  "range and arm swing, exactly matching the gait and emotion literature."),
        dict(caption="Why the black box struggles",
             text="On the raw data, the main variation captures the actor and the "
                  "camera setup, not the emotion. That is why black-box methods "
                  "struggle here."),
        dict(caption="Takeaways",
             bullets=["Small data: expert knowledge wins",
                      "PCA beats raw NN: curse of dimensionality",
                      "Autoencoder learns useful, but not expert-level, features"],
             text="The big lesson: when data is small, hand-designed expert features "
                  "beat black-box deep learning. To overtake them, we would need much "
                  "more data, or models that use the time structure of the walk. Thank you."),
    ],
)

JA = dict(
    voice="Kyoko", base_rate=180, rate_lo=150, rate_hi=260,
    out="summary_video_ja.mp4",
    slides=[
        dict(caption="表現的歩行からの感情推定",
             bullets=["Homework-2", "歩き方から感情を分類する",
                      "College de France 表現的歩行データベース"],
             text="感情は歩き方にどう表れるのでしょうか。コレージュ・ド・フランスの"
                  "表現的歩行データベースを使い、歩行から感情を分類します。"),
        dict(caption="使用データ",
             bullets=["41個のマーカー・3次元・30fps",
                      "4名 × 4感情 × 約5試行 = 81歩行",
                      "感情：怒り・喜び・中立・悲しみ"],
             text="各歩行は41個のマーカーを3次元で記録。4名の俳優が怒り、喜び、中立、"
                  "悲しみを演じ、合計81試行です。"),
        dict(caption="2つの特徴哲学を公平に比較",
             text="特徴の作り方を2通り比較します。専門家特徴は、生体力学にもとづく"
                  "25個の手作りの数値。ブラックボックスは、生のマーカー軌跡、約8000個の数値です。"),
        dict(caption="主成分分析（PCA）",
             text="生データには主成分分析を使い、変動の大きい20方向だけを残して次元を減らします。"),
        dict(caption="k近傍法",
             text="そのうえで、最も近い5つの歩行で多数決する単純な分類器を使います。"),
        dict(caption="ランダムフォレスト",
             text="専門家特徴にはランダムフォレスト。数百本の決定木が多数決します。"),
        dict(caption="ロジスティック回帰",
             text="ロジスティック回帰も使います。特徴をクラス確率に変換する線形モデルです。"),
        dict(caption="ニューラルネット",
             text="ブラックボックスでは、ニューラルネットが生のマーカーから直接学習します。"
                  "知識は加えません。"),
        dict(caption="オートエンコーダ",
             text="オートエンコーダは、ラベルを見ずに生データを16個の数値へ圧縮します。"),
        dict(caption="公平な評価",
             bullets=["Leave-One-Subject-Out 交差検証",
                      "3名で学習し、残り1名でテスト",
                      "『誰か』ではなく『どの感情か』を測る"],
             text="評価はリーブ・ワン・サブジェクト・アウト。3名で学習し、残る1名でテスト。"
                  "人物ではなく感情を測ります。"),
        dict(caption="結果",
             text="結果は明確です。専門家特徴とランダムフォレストは91パーセント。"
                  "純粋なニューラルネットは40パーセントで、偶然をわずかに上回る程度です。"),
        dict(caption="最良モデルの混同行列",
             text="悲しみはほぼ完全に認識。混同は怒りと喜びの間で、"
                  "どちらも覚醒度の高い感情です。"),
        dict(caption="効いた特徴",
             text="効いた特徴は、運動エネルギー、体幹の傾き、肘の可動域、腕の振り。"
                  "歩行と感情の研究と一致します。"),
        dict(caption="ブラックボックスが苦戦する理由",
             text="生データでは、主な変動が感情ではなく俳優やカメラ設定を捉えています。"
                  "だからブラックボックスは苦戦します。"),
        dict(caption="まとめ",
             bullets=["小データでは専門知識が勝つ",
                      "PCAは生NNに勝つ：次元の呪い",
                      "AEは有用だが専門特徴には届かない"],
             text="教訓です。データが少ないとき、専門家特徴は深層学習に勝ります。"
                  "超えるには、より多くのデータか、時間構造を使うモデルが必要です。"
                  "ご清聴ありがとうございました。"),
    ],
)

LANGS = {"en": EN, "ja": JA}


# ---------------------------------------------------------------------------
def render_slide(caption, img, bullets, path):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.93, caption, ha="center", va="center",
             fontsize=26, fontweight="bold", color="#1f3b5c")
    if img:
        ax = fig.add_axes([0.04, 0.04, 0.92, 0.82])
        ax.imshow(plt.imread(img))
        ax.axis("off")
    else:
        for i, b in enumerate(bullets or []):
            fig.text(0.5, 0.66 - i * 0.13, "•  " + b, ha="center", va="center",
                     fontsize=22, color="#222222")
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def synth(text, voice, rate, wav_path):
    """macOS say -> AIFF -> padded WAV; return duration (s, incl. PAD)."""
    aiff = wav_path + ".aiff"
    run(["say", "-v", voice, "-r", str(rate), "-o", aiff, text])
    run([FFMPEG, "-y", "-i", aiff, "-af", f"apad=pad_dur={PAD}",
         "-ar", "44100", "-ac", "2", wav_path])
    os.remove(aiff)
    with wave.open(wav_path) as w:
        return w.getnframes() / w.getframerate()


def build(cfg):
    tmp = tempfile.mkdtemp(prefix="hw2vid_")
    slides = cfg["slides"]
    n = len(slides)
    pads = n * PAD

    # Pass 1: measure speech at the base rate, then rescale rate to hit T_FINAL.
    durs = [synth(s["text"], cfg["voice"], cfg["base_rate"],
                  os.path.join(tmp, f"a{i:02d}.wav")) for i, s in enumerate(slides)]
    speech = sum(durs) - pads
    scale = speech / max(1.0, (T_FINAL - pads))
    rate = int(min(cfg["rate_hi"], max(cfg["rate_lo"], round(cfg["base_rate"] * scale))))
    print(f"[{cfg['voice']}] {n} slides, base speech {speech:.0f}s -> rate {rate} wpm")

    # Pass 2: regenerate at the fitted rate and build per-slide clips.
    seg_mp4s, total = [], 0.0
    for i, s in enumerate(slides):
        slide = os.path.join(tmp, f"s{i:02d}.png")
        wav = os.path.join(tmp, f"s{i:02d}.wav")
        mp4 = os.path.join(tmp, f"s{i:02d}.mp4")
        render_slide(s["caption"], IMAGES[i], s.get("bullets"), slide)
        dur = synth(s["text"], cfg["voice"], rate, wav)
        total += dur
        run([FFMPEG, "-y", "-loop", "1", "-i", slide, "-i", wav,
             "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac",
             "-b:a", "192k", "-pix_fmt", "yuv420p", "-r", "30", "-shortest",
             "-vf", f"scale={W}:{H}", mp4])
        seg_mp4s.append(mp4)
        print(f"  slide {i:02d}  {dur:5.1f}s  {s['caption']}")

    listfile = os.path.join(tmp, "list.txt")
    with open(listfile, "w") as f:
        for m in seg_mp4s:
            f.write(f"file '{m}'\n")
    out_mp4 = os.path.join(ROOT, cfg["out"])
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
         "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", out_mp4])

    mm, ss = divmod(round(total), 60)
    print(f"Total ~ {int(mm)}:{int(ss):02d} ({total:.1f}s) -> {cfg['out']}\n")
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    if lang not in LANGS:
        sys.exit(f"unknown language '{lang}' (use: en | ja)")
    build(LANGS[lang])


if __name__ == "__main__":
    main()
