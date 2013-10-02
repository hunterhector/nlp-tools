package edu.cmu.lti.event_coref.analysis_engine.annotator;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.uima.UimaContext;
import org.apache.uima.analysis_engine.AnalysisEngineProcessException;
import org.apache.uima.jcas.JCas;
import org.apache.uima.resource.ResourceInitializationException;
import org.uimafit.component.JCasAnnotator_ImplBase;
import org.uimafit.descriptor.ConfigurationParameter;
import org.uimafit.util.JCasUtil;

import com.google.common.collect.ArrayListMultimap;

import tratz.parse.FullSystemWrapper;
import tratz.parse.FullSystemWrapper.FullSystemResult;
import tratz.parse.types.Arc;
import tratz.parse.types.Parse;
import tratz.parse.types.Token;
import edu.cmu.lti.event_coref.type.FanseDependencyRelation;
import edu.cmu.lti.event_coref.type.FanseSemanticRelation;
import edu.cmu.lti.event_coref.type.FanseToken;
import edu.cmu.lti.event_coref.type.StanfordCorenlpSentence;
import edu.cmu.lti.event_coref.type.StanfordCorenlpToken;
import edu.cmu.lti.event_coref.type.Word;
import edu.cmu.lti.util.general.LogUtils;
import edu.cmu.lti.util.uima.FSCollectionFactory;
import edu.cmu.lti.util.uima.UimaConvenience;

/**
 * Runs FANSE parser, and annotate associated types.
 * 
 * Required annotation: sentence, token
 */
public class FanseAnnotator extends JCasAnnotator_ImplBase {

  public static final String PARAM_MODEL_BASE_DIR = "modelBaseDirectory";

  @ConfigurationParameter(name = PARAM_MODEL_BASE_DIR)
  private String modeBaseDir;

  // these file are assume existence in the base directory
  private static final String POS_MODEL = "posTaggingModel.gz", PARSE_MODEL = "parseModel.gz",
          POSSESSIVES_MODEL = "possessivesModel.gz", NOUN_COMPOUND_MODEL = "nnModel.gz",
          SRL_ARGS_MODELS = "srlArgsWrapper.gz", SRL_PREDICATE_MODELS = "srlPredWrapper.gz",
          PREPOSITION_MODELS = "psdModels.gz", WORDNET = "data/wordnet3";

  public final static Boolean DEFAULT_VCH_CONVERT = Boolean.FALSE;

  public final static String DEFAULT_SENTENCE_READER_CLASS = tratz.parse.io.ConllxSentenceReader.class
          .getName();

  FullSystemWrapper fullSystemWrapper = null;

  public void initialize()  {
    try {
      fullSystemWrapper = new FullSystemWrapper(modeBaseDir + PREPOSITION_MODELS, modeBaseDir
              + NOUN_COMPOUND_MODEL, modeBaseDir + POSSESSIVES_MODEL,
              modeBaseDir + SRL_ARGS_MODELS, modeBaseDir + SRL_PREDICATE_MODELS, modeBaseDir
                      + POS_MODEL, modeBaseDir + PARSE_MODEL, modeBaseDir + WORDNET);
    } catch (Exception e) {
      e.printStackTrace();
    }
  }

  public void process(JCas aJCas) {
    UimaConvenience.printProcessLog(aJCas);

    List<StanfordCorenlpSentence> sentList = UimaConvenience.getAnnotationList(aJCas,
            StanfordCorenlpSentence.class);

    for (StanfordCorenlpSentence sent : sentList) {
      List<StanfordCorenlpToken> tokenList = JCasUtil.selectCovered(StanfordCorenlpToken.class,
              sent);

      Parse par = tokenListToParse(tokenList);
      tratz.parse.types.Sentence fSent = par.getSentence();
      List<Token> tokens = fSent.getTokens();

      FullSystemResult result = fullSystemWrapper.process(fSent, tokens.size() > 0
              && tokens.get(0).getPos() == null, true, true, true, true, true);

      Parse dependencyParse = result.getParse();
      Parse semanticParse = result.getSrlParse();

      tratz.parse.types.Sentence resultSent = dependencyParse.getSentence();
      List<Token> resultTokens = resultSent.getTokens();

      // get Token annotation and convert them to UIMA
      Map<Token, FanseToken> Fanse2UimaMap = new HashMap<Token, FanseToken>();
      int tokenId = 1;
      for (Token token : resultTokens) {
        StanfordCorenlpToken sToken = tokenList.get(token.getIndex() - 1);
        String fTokenStr = token.getText();
        String sTokenStr = sToken.getCoveredText();
        if (!fTokenStr.equals(sTokenStr)) {
          LogUtils.logError("The Fanse token is different from the Stanford token. Fanse token: "
                  + fTokenStr + ", Stanford token: " + sTokenStr);
        }

        int begin = sToken.getBegin();
        int end = sToken.getEnd();
        FanseToken fToken = new FanseToken(aJCas, begin, end);
        fToken.setTokenId(tokenId);
        fToken.setCoarsePos(token.getCoarsePos());
        fToken.setPos(token.getPos());
        fToken.setLexicalSense(token.getLexSense());
        fToken.addToIndexes();
        tokenId++;

        Fanse2UimaMap.put(token, fToken);
      }

      // now create depedency edges of these nodes
      // Map<FanseToken, List<FanseDepedencyRelation>> dependencyHeadRelationMap = new
      // HashMap<FanseToken, List<FanseDepedencyRelation>>();
      // Map<FanseToken, List<FanseDepedencyRelation>> dependencyChildRelationMap = new
      // HashMap<FanseToken, List<FanseDepedencyRelation>>();

      ArrayListMultimap<FanseToken, FanseDependencyRelation> dependencyHeadRelationMap = ArrayListMultimap
              .create();
      ArrayListMultimap<FanseToken, FanseDependencyRelation> dependencyChildRelationMap = ArrayListMultimap
              .create();

      for (Arc arc : dependencyParse.getArcs()) {
        if (arc != null) {
          FanseToken childToken = Fanse2UimaMap.get(arc.getChild());
          FanseToken headToken = Fanse2UimaMap.get(arc.getHead());

          if (childToken != null || headToken != null) {
            FanseDependencyRelation fArc = new FanseDependencyRelation(aJCas);
            fArc.setHead(headToken);
            fArc.setChild(childToken);
            fArc.setDependency(arc.getDependency());

            dependencyHeadRelationMap.put(childToken, fArc);
            dependencyChildRelationMap.put(headToken, fArc);

            fArc.addToIndexes(aJCas);
          }
        }
      }

      // now creat semantic edges of these nodes
      // Map<FanseToken, List<FanseSemanticRelation>> semanticHeadRelationMap = new
      // HashMap<FanseToken, List<FanseSemanticRelation>>();
      // Map<FanseToken, List<FanseSemanticRelation>> semanticChildRelationMap = new
      // HashMap<FanseToken, List<FanseSemanticRelation>>();

      ArrayListMultimap<FanseToken, FanseSemanticRelation> semanticHeadRelationMap = ArrayListMultimap
              .create();
      ArrayListMultimap<FanseToken, FanseSemanticRelation> semanticChildRelationMap = ArrayListMultimap
              .create();

      for (Arc arc : semanticParse.getArcs()) {
        if (arc != null && arc.getSemanticAnnotation() != null) {
          FanseToken childToken = Fanse2UimaMap.get(arc.getChild());
          FanseToken headToken = Fanse2UimaMap.get(arc.getHead());

          if (childToken != null || headToken != null) {
            FanseSemanticRelation fArc = new FanseSemanticRelation(aJCas);
            fArc.setHead(headToken);
            fArc.setChild(childToken);
            fArc.setSemanticAnnotation(arc.getSemanticAnnotation());

            semanticHeadRelationMap.put(childToken, fArc);
            semanticChildRelationMap.put(headToken, fArc);

            fArc.addToIndexes(aJCas);
          }
        }
      }

      // associate token annotation with arc
      for (FanseToken fToken : Fanse2UimaMap.values()) {
        if (dependencyHeadRelationMap.containsKey(fToken)) {
          fToken.setHeadDependencyRelations(FSCollectionFactory.createFSList(aJCas,
                  dependencyHeadRelationMap.get(fToken)));
        }
        if (dependencyChildRelationMap.containsKey(fToken)) {
          fToken.setChildDependencyRelations(FSCollectionFactory.createFSList(aJCas,
                  dependencyChildRelationMap.get(fToken)));
        }
        if (semanticHeadRelationMap.containsKey(fToken)) {
          fToken.setHeadSemanticRelations(FSCollectionFactory.createFSList(aJCas,
                  semanticHeadRelationMap.get(fToken)));
        }
        if (semanticChildRelationMap.containsKey(fToken)) {
          fToken.setChildSemanticRelations(FSCollectionFactory.createFSList(aJCas,
                  semanticChildRelationMap.get(fToken)));
        }

        fToken.addToIndexes(aJCas);
      }
    }
  }

  private Parse wordListToParse(List<Word> words) {
    Token root = new Token("[ROOT]", 0);
    List<Token> tokens = new ArrayList<Token>();
    List<Arc> arcs = new ArrayList<Arc>();

    int tokenNum = 0;
    for (Word word : words) {
      tokenNum++;
      String wordString = word.getCoveredText();
      Token token = new Token(wordString, tokenNum);
      tokens.add(token);
    }

    // Currently does not implement the Quote converstion by Tratz in TokenizingSentenceReader
    // line = mDoubleQuoteMatcher.reset(line).replaceAll("\"");
    // line = mSingleQuoteMatcher.reset(line).replaceAll("'");

    Parse result = new Parse(new tratz.parse.types.Sentence(tokens), root, arcs);

    return result;
  }

  private Parse tokenListToParse(List<StanfordCorenlpToken> tokenList) {
    Token root = new Token("[ROOT]", 0);
    List<Token> tokens = new ArrayList<Token>();
    List<Arc> arcs = new ArrayList<Arc>();

    int tokenNum = 0;
    for (StanfordCorenlpToken stanfordToken : tokenList) {
      tokenNum++;
      String wordString = stanfordToken.getCoveredText();
      Token token = new Token(wordString, tokenNum);
      tokens.add(token);
    }

    // Currently does not implement the Quote converstion by Tratz in TokenizingSentenceReader
    // line = mDoubleQuoteMatcher.reset(line).replaceAll("\"");
    // line = mSingleQuoteMatcher.reset(line).replaceAll("'");

    Parse result = new Parse(new tratz.parse.types.Sentence(tokens), root, arcs);

    return result;
  }

}
