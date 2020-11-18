// This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK (v2).
// Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
// session persistence, api calls, and more.
const Alexa = require('ask-sdk-core');
const Util = require('util.js');

const AudioName = 'meisou1.mp3';//将来的に他の瞑想も実装する。その時は配列で管理しようと考えている。


const LaunchRequestHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'LaunchRequest';
    },
    handle(handlerInput) {
        
        
        var speakOutput = '瞑想サプリへようこそ！。このスキルはあなたの瞑想をサポートします。瞑想を始めたいときは「瞑想する。」、使い方を知りたいときは「ヘルプ。」と言ってください。';
        //変なこと喋らせてるけと全体公開のときは変える。
        //初回だけ喋らせる
        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};
/*
const HelloWorldIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'HelloWorldIntent';
    },
    handle(handlerInput) {
        const speakOutput = 'Hello World!';
        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
};
*/

const medIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'medIntent';
    },
    async handle(handlerInput) {
        var preSpeak = '<audio src="soundbank://soundlibrary/musical/amzn_sfx_church_bell_1x_03"/><break time="3s"/>';//初めにかける言葉
        //var endSpeak = '<audio src="soundbank://soundlibrary/musical/amzn_sfx_church_bell_1x_03"/><say-as interpret-as="interjection">お疲れさまでした</say-as>';
        //終わったあとに掛ける言葉
        //何回瞑想したかを計測する機能もほしい
        const Url = Util.getS3PreSignedUrl('Media/audio/' + AudioName);
        const token = "sample";
        console.log(Url);
        return handlerInput.responseBuilder
            .speak(preSpeak)
            .addAudioPlayerPlayDirective('REPLACE_ALL', Url, token, 0, null)
            .getResponse();
    }
};

//Audioインターフェースを実装するとき必ず必要
//普通は実行されない想定
const PauseIntentHandler = {
    canHandle(handlerInput) {
        const request = handlerInput.requestEnvelope.request;
        return (request.type === 'IntentRequest' && request.intent.name === 'AMAZON.PauseIntent');
    },
    async handle(handlerInput) {
        return handlerInput.responseBuilder
        .addAudioPlayerStopDirective()
        //.speak('サンプルを中断します。')
        .getResponse();
    }
};
//Audioインターフェースを実装するとき必ず必要
//普通は実行されない想定
const ResumeIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.ResumeIntent';
    },
    async handle(handlerInput) {
        const Url = Util.getS3PreSignedUrl('Media/audio/' + AudioName);
        const AudioPlayer = handlerInput.requestEnvelope.context.AudioPlayer;
        const token = AudioPlayer.token;
        const offset = AudioPlayer.offsetInMilliseconds;
        return handlerInput.responseBuilder
            .addAudioPlayerPlayDirective('REPLACE_ALL', Url, token, offset, null)
            //.speak('再開します')
            .getResponse();
  }
};
//Audioインターフェースを実装するとき必ず必要
//普通は実行されない想定
//Audioインターフェースを実装するとき必要。なぜかこれがないとエラーが起こる。
const PlaybackHandler = {
  canHandle(handlerInput) {
      const type = handlerInput.requestEnvelope.request.type;
      return (type === 'AudioPlayer.PlaybackStarted' || // 再生開始
              type === 'AudioPlayer.PlaybackFinished' || // 再生終了
              type === 'AudioPlayer.PlaybackStopped' || // 再生停止
              type === 'AudioPlayer.PlaybackNearlyFinished' || // もうすぐ再生終了
              type === 'AudioPlayer.PlaybackFailed'); // 再生失敗
  },
  async handle(handlerInput) {
      return handlerInput.responseBuilder
      .getResponse();
  }
};

const HelpIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.HelpIntent';
    },
    handle(handlerInput) {
        var speakOutput = 'このスキルは慈悲の瞑想をサポートしています。';
        speakOutput += `瞑想を始めたいときは「瞑想をする」と言ってください`;
        var respeakOutput = `「瞑想をする」と言うと瞑想を始めることができます。。`;
        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(respeakOutput)
            .getResponse();
    }
};
const CancelAndStopIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && (Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.CancelIntent'
                || Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.StopIntent');
    },
    handle(handlerInput) {
        const speakOutput = '<say-as interpret-as="interjection">またいつでもどうぞ</say-as>.';//スピーコンを実装する
        return handlerInput.responseBuilder
            .addAudioPlayerStopDirective()//キャンセルでも音を消す
            .speak(speakOutput)
            .getResponse();
    }
};
const SessionEndedRequestHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'SessionEndedRequest';
    },
    handle(handlerInput) {
        // Any cleanup logic goes here.
        return handlerInput.responseBuilder.getResponse();
    }
};

// The intent reflector is used for interaction model testing and debugging.
// It will simply repeat the intent the user said. You can create custom handlers
// for your intents by defining them above, then also adding them to the request
// handler chain below.
const IntentReflectorHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest';
    },
    handle(handlerInput) {
        const intentName = Alexa.getIntentName(handlerInput.requestEnvelope);
        const speakOutput = `You just triggered ${intentName}`;

        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
};

// Generic error handling to capture any syntax or routing errors. If you receive an error
// stating the request handler chain is not found, you have not implemented a handler for
// the intent being invoked or included it in the skill builder below.
const ErrorHandler = {
    canHandle() {
        return true;
    },
    handle(handlerInput, error) {
        console.log(`~~~~ Error handled: ${error.stack}`);
        const speakOutput = `Sorry, I had trouble doing what you asked. Please try again.~~~~ Error handled: ${error.stack}`;

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};

// The SkillBuilder acts as the entry point for your skill, routing all request and response
// payloads to the handlers above. Make sure any new handlers or interceptors you've
// defined are included below. The order matters - they're processed top to bottom.
exports.handler = Alexa.SkillBuilders.custom()
    .addRequestHandlers(
        LaunchRequestHandler,
        medIntentHandler,
        PauseIntentHandler,
        ResumeIntentHandler,
        PlaybackHandler,
        HelpIntentHandler,
        CancelAndStopIntentHandler,
        SessionEndedRequestHandler,
        IntentReflectorHandler, // make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
    )
    .addErrorHandlers(
        ErrorHandler,
    )
    .lambda();