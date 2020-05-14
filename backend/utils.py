import os
import six
import langdetect
from backend.data import Video
from wordcloud import WordCloud
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

# Sentiment analysis mark scale and magnitude scale
EN_FONT = 'CODE Light.otf'
CH_FONT = 'STKAITI.TTF'
SCORE_SCALE = [-0.5, -0.3, -0.1, 0.1, 0.3, 0.5]


# TODO(harry) update api call
def extract_all_descriptive_words(text) -> str:
    """Detects syntax in the text and pull out all adjectives.
    """
    client = language.LanguageServiceClient()

    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')

    # Instantiates a plain text document.
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects syntax in the document.
    tokens = client.analyze_syntax(document).tokens

    res = ''
    for token in tokens:
        part_of_speech_tag = enums.PartOfSpeech.Tag(token.part_of_speech.tag)
        if part_of_speech_tag.name == 'ADJ':
            res += f'{token.text.content} '
    return res


# TODO(harry) update api call
def sentiment_analysis(text: str) -> tuple:
    """Detects sentiment in the text."""
    length = text.count(' ') + 1
    client = language.LanguageServiceClient()

    # Instantiates a plain text document.
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects sentiment in the document. You can also analyze HTML with:
    #   document.type == enums.Document.Type.HTML
    sentiment = client.analyze_sentiment(document).document_sentiment
    if not sentiment:
        return "", ""
    else:
        score = sentiment.score
        magnitude = sentiment.magnitude

        saturation = magnitude / length > 0.1

        if score <= SCORE_SCALE[0]:
            return "Audiences have apparently negative reviews", "&#x1f620"
        elif SCORE_SCALE[0] < score <= SCORE_SCALE[1]:
            return "The reviews are somewhat negative", "&#x2639"
        elif SCORE_SCALE[1] < score < SCORE_SCALE[2]:
            return "The reviews are slightly negative", "&#x1f641"
        elif SCORE_SCALE[2] <= score <= SCORE_SCALE[3]:
            if saturation:
                return "Audiences have mixed reviews", "&#x1f928"
            else:
                return "Audiences are neutral", "&#x1f636"
        elif SCORE_SCALE[3] < score <= SCORE_SCALE[4]:
            return "Reviews are pretty positive~", "&#128578"
        else:
            return "Reviews are complimenting!", "&#x1f604"


def generate_word_cloud(filename: str, text: str, lang: str) -> str:
    """Function to generate word cloud and returns the path to the image.
    """
    # confirm directory
    this_path = os.path.abspath(os.path.dirname(__file__))

    stopwords_file = os.path.join(this_path, rf"..\dat\\{['en', 'zh-cn'][lang == 'zh-cn']}_stopwords.txt")
    file_out_path = os.path.join(this_path, r"..\frontend\pics\{}.png".format(filename))
    # bg_image_path = os.path.join(this_path, r"..\dat\wcloud_bg.jpg")

    if lang == "zh-cn":
        font_path = os.path.join(this_path, rf"..\dat\\{CH_FONT}")
    else:
        font_path = os.path.join(this_path, rf"..\dat\\{EN_FONT}")

    # background_image = plt.imread(bg_image_path)
    # fetch all stopwords
    stopwords = set("")
    if lang == "en":
        with open(stopwords_file) as file:
            words = [word.rstrip() for word in file.readlines()]
        stopwords.update(words)

    wc = WordCloud(
        background_color="white",
        font_path=font_path,
        max_words=2000,
        width=1000,
        height=800,
        max_font_size=150,
        random_state=10,
        stopwords=stopwords
    )

    wc.generate_from_text(text)

    # process_word = WordCloud.process_text(wc, text)
    # sorted_keywords = sorted(process_word.items(), key=lambda e: e[1], reverse=True)
    # print(sorted_keywords[:50])
    # img_colors = ImageColorGenerator(background_image)
    # wc.recolor(color_func=img_colors)

    wc.to_file(file_out_path)

    return "%s.png" % filename


def detect_lang(video: Video) -> None:
    """Helper function to detect the language of the majority oof the comments.
    """
    video.lang = langdetect.detect(video.title)


def analysis(video) -> tuple:
    """Function to perform analysis."""
    detect_lang(video)

    if video.lang:
        # generate word cloud
        comment_text = " ".join(video.__dict__.get("comments"))

        filename = generate_word_cloud(
            video.id_.get_id(), extract_all_descriptive_words(comment_text), video.lang)
    else:
        filename = ""

    # sentiment analysis
    return sentiment_analysis(comment_text), filename


if __name__ == "__main__":
    pass
