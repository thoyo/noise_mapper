import matplotlib.pyplot as plt
import main
import os
import audio2numpy as a2n
import numpy as np


def mp4_to_plot():
    plt.figure()
    ax1 = plt.subplot(121)
    ax2 = plt.subplot(122)
    for filename in os.listdir("../data"):
        if filename.startswith("quiet_"):
            ax1.plot(main.mp4_audio_to_arr(f"../data/{filename}")[:, 0])
        elif filename.startswith("noisy_"):
            ax2.plot(main.mp4_audio_to_arr(f"../data/{filename}")[:, 0])

    plt.show()


def mp3_to_plot():
    noisy_means = quiet_means = 0
    noisy_stds = quiet_stds = 0
    noisy_medians = quiet_medians = 0
    noisy_sum = quiet_sum = 0
    noisy_means_vec = []
    quiet_means_vec = []
    noisy_stds_vec = []
    quiet_stds_vec = []
    noisy_medians_vec = []
    quiet_medians_vec = []
    noisy_sum_vec = []
    quiet_sum_vec = []
    noisy_samples = 0
    quiet_samples = 0
    plt.figure()
    ax1 = plt.subplot(121)
    plt.ylim(top=0.6)
    ax2 = plt.subplot(122)
    plt.ylim(top=0.6)
    for filename in os.listdir("../data"):
        if filename.endswith(".mp4"):
            continue
        x, sr = a2n.audio_from_file(f"../data/{filename}")
        len_s = x.shape[0] / sr
        if len_s < 4 or len_s > 6:
            continue
        x = np.abs(x[:, 0])
        print(f"{filename}, {x.shape[0] / sr}")
        if filename.startswith("quiet_"):
            ax1.plot(x)
            quiet_means = (quiet_means * quiet_samples + np.mean(x)) / (quiet_samples + 1)
            quiet_means_vec.append(np.mean(x))
            quiet_stds = (quiet_stds * quiet_samples + np.std(x)) / (quiet_samples + 1)
            quiet_stds_vec.append(np.std(x))
            quiet_medians = (quiet_medians * quiet_samples + np.median(x)) / (quiet_samples + 1)
            quiet_medians_vec.append(np.median(x))
            quiet_samples += 1
            quiet_sum += np.sum(x)
            quiet_sum_vec.append(np.sum(x))
        elif filename.startswith("noisy_"):
            ax2.plot(x)
            noisy_means = (noisy_means * noisy_samples + np.mean(x)) / (noisy_samples + 1)
            noisy_means_vec.append(np.mean(x))
            noisy_stds = (noisy_stds * noisy_samples + np.std(x)) / (noisy_samples + 1)
            noisy_stds_vec.append(np.std(x))
            noisy_medians = (noisy_medians * noisy_samples + np.median(x)) / (noisy_samples + 1)
            noisy_medians_vec.append(np.median(x))
            noisy_sum += np.sum(x)
            noisy_sum_vec.append(np.sum(x))

    print(f"mean: {quiet_means}, {noisy_means}")
    print(f"std: {quiet_stds}, {noisy_stds}")
    print(f"median: {quiet_medians}, {noisy_medians}")
    print(f"sum: {quiet_sum}, {noisy_sum}")

    plt.show()

    plt.figure()
    plt.subplot(421)
    plt.ylim(top=0.025)
    plt.plot(quiet_means_vec)

    plt.subplot(422)
    plt.ylim(top=0.025)
    plt.plot(noisy_means_vec)

    plt.subplot(423)
    plt.ylim(top=0.035)
    plt.plot(quiet_stds_vec)

    plt.subplot(424)
    plt.ylim(top=0.035)
    plt.plot(noisy_stds_vec)

    plt.subplot(425)
    plt.ylim(top=0.015)
    plt.plot(quiet_medians_vec)

    plt.subplot(426)
    plt.ylim(top=0.015)
    plt.plot(noisy_medians_vec)

    plt.subplot(427)
    plt.ylim(top=4500)
    plt.plot(quiet_sum_vec)

    plt.subplot(428)
    plt.ylim(top=4500)
    plt.plot(noisy_sum_vec)

    plt.show()
    plt.ylim(top=0.015)
    plt.ylim(top=0.6)


if __name__ == "__main__":
    mp3_to_plot()
