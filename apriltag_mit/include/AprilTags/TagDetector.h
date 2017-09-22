#ifndef APRILTAGS_TAGDETECTOR_H_
#define APRILTAGS_TAGDETECTOR_H_

#include <opencv2/core/core.hpp>
#include <unordered_map>

#include "AprilTags/DisjointSets.h"
#include "AprilTags/FloatImage.h"
#include "AprilTags/GrayModel.h"
#include "AprilTags/Quad.h"
#include "AprilTags/TagDetection.h"
#include "AprilTags/TagFamily.h"

namespace AprilTags {

class TagDetector {
 public:
  using Clusters = std::unordered_map<int, std::vector<cv::Point3f>>;
  using TagDetectionVec = std::vector<TagDetection>;

  explicit TagDetector(const TagCodes& tag_codes, unsigned black_border = 1);

  TagDetectionVec ExtractTags(const cv::Mat& image) const;

  void set_black_border(unsigned black_border) { black_border_ = black_border; }
  unsigned black_border() const { return black_border_; }

 private:
  const TagFamily tag_family_;

  int CalcFilterSize(float sigma) const;

  /**
   * @brief Preprocess Step 1
   * @param image
   * @param im_decode
   * @param im_segment
   */
  void Preprocess(const FloatImage& image, FloatImage& im_decode,
                  FloatImage& im_segment) const;

  /**
   * @brief CalcPolar Step 2
   * @param image
   * @param im_mag
   * @param im_theta
   */
  void CalcPolar(const FloatImage& image, FloatImage& im_mag,
                 FloatImage& im_theta) const;

  /**
   * @brief ExtractEdges Step 3
   * @param im_mag
   * @param im_theta
   * @return
   */
  DisjointSets ExtractEdges(const FloatImage& im_mag,
                            const FloatImage& im_theta) const;

  /**
   * @brief ClusterPixels Step 4
   * @param uf
   * @param im_mag
   * @return
   */
  Clusters ClusterPixels(DisjointSets& uf, const FloatImage& im_mag) const;

  /**
   * @brief FitLines Step 5
   * @param clusters
   * @return
   */
  std::vector<Segment> FitLines(const Clusters& clusters,
                                const FloatImage& im_mag,
                                const FloatImage& im_theta) const;

  /**
   * @brief ChainSegments Step 6
   * @param segments
   */
  void ChainSegments(std::vector<Segment>& segments,
                     const FloatImage& image) const;

  /**
   * @brief SearchQuads Step 7
   * @param segments
   * @return
   */
  std::vector<Quad> SearchQuads(std::vector<Segment>& segments) const;

  /**
   * @brief DecodeQuads Step 8
   * @param quads
   * @return
   */
  std::vector<TagDetection> DecodeQuads(const std::vector<Quad>& quads,
                                        const FloatImage& image) const;

  /**
   * @brief ResolveOverlap Step 9
   * @param detections
   * @return
   */
  TagDetectionVec ResolveOverlap(const TagDetectionVec& detections) const;

  /**
   * @brief black_border_ Number of bits of black border of the tag
   */
  unsigned black_border_ = 1;

  /**
   * @brief decode_sigma_ Gaussian smoothing kernel applied to image
   * Used when sampling bits. Filtering is a good idea in cases where A) a cheap
   * camera is introducing artificial sharpening, B) the bayer pattern is
   * creating artifacts, C) the sensor is very noisy and/or has hot/cold pixels.
   * However, filtering makes it harder to decode very small tags. Resonable
   * values are 0, 0.8, 1.5
   */
  float decode_sigma_ = 0.8f;

  /**
   * @brief segment_sigma_ Gaussian smoothing kernel applied to image
   * Used when detecting the outline of the box. It is almost always useful to
   * have some filtering, since the loss of small details won't hurt.
   * Recommended value is 0.8.
   */
  float segment_sigma_ = 0.8f;
};

void ConvertToGray(cv::InputArray in, cv::OutputArray out);

std::vector<int> IndexFromNonZero(const cv::Mat mat);

}  // namespace AprilTags

#endif  // APRILTAGS_TAGDETECTOR_H_
