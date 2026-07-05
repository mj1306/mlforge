const modelDescriptions = {
  // YOLO models
  YOLOv3: `YOLOv3 is a real-time object detection system developed by Joseph Redmon.
It uses Darknet-53 as its backbone and predicts bounding boxes at three different scales.
YOLOv3 introduces multi-label classification using logistic regression and performs
well for detecting small objects. It is faster than most two-stage detectors while
retaining reasonable accuracy, making it suitable for embedded and real-time applications.`,

  YOLOv4: `YOLOv4 improves upon YOLOv3 by integrating multiple modern techniques such as
CSPDarknet53 backbone, PANet neck, Mish activation, and mosaic data augmentation.
It balances speed and accuracy for real-time object detection tasks. YOLOv4 can
achieve state-of-the-art results on the COCO dataset and is highly optimized for GPU
training and deployment.`,

  YOLOv5: `YOLOv5 is a PyTorch implementation of YOLO designed for flexibility and efficiency.
It introduces modules such as SPPF (Spatial Pyramid Pooling Fast) and PANet for better
feature aggregation. YOLOv5 supports automatic mixed precision training, hyperparameter
auto-tuning, and modular architecture, making it widely used in production and research.`,

  YOLOv6: `YOLOv6 focuses on lightweight and efficient real-time object detection.
It includes optimized backbones, improved neck structures, and efficient training
strategies. YOLOv6 models are suitable for edge devices and resource-constrained
environments while maintaining competitive accuracy.`,

  YOLOv7: `YOLOv7 introduces new techniques such as E-ELAN modules and model scaling
strategies. It achieves higher accuracy and faster inference compared to its
predecessors. YOLOv7 is designed for real-time applications, providing a robust
solution for detection in diverse environments.`,

  YOLOv8: `YOLOv8 focuses on both accuracy and speed, using CSPDarknet53 backbone and
SPPF+PANet neck. It features improved layer structures, advanced augmentation,
and better anchor strategies. YOLOv8 provides excellent performance for real-time
object detection with high mAP.`,

  YOLOv9: `YOLOv9 introduces programmable gradient information (PGI) for better training
dynamics. It is optimized for high-performance detection tasks with a focus on
accuracy, computational efficiency, and scalability across multiple model sizes.`,

  YOLOv10: `YOLOv10 emphasizes real-time end-to-end object detection with optimized
backbone and neck designs. It supports larger input sizes and improved feature
aggregation for enhanced detection accuracy on complex datasets.`,

  YOLOv11: `YOLOv11 further enhances detection performance with refined architectures,
improved training strategies, and better generalization. It is suitable for industrial
applications requiring both speed and high precision.`,

  // ResNet models
  ResNet18: `ResNet18 is a deep residual network with 18 layers that uses skip connections
to mitigate vanishing gradients. It is lightweight and widely used for image
classification tasks where moderate accuracy is sufficient and computation resources
are limited.`,

  ResNet34: `ResNet34 increases depth to 34 layers, maintaining the residual block
structure. It provides higher accuracy than ResNet18 while still being efficient
enough for moderate-sized datasets and applications requiring lower computational
overhead.`,

  ResNet50: `ResNet50 is a 50-layer deep residual network introducing bottleneck blocks.
It balances accuracy and efficiency, making it a popular backbone for tasks such as
object detection, segmentation, and recognition. It achieves strong performance
on ImageNet and other benchmarks.`,

  ResNet101: `ResNet101 expands to 101 layers with deeper bottleneck architectures.
It improves feature representation, enabling higher accuracy for complex visual
tasks. ResNet101 is often used in research and production where high accuracy
is required.`,

  ResNet152: `ResNet152 is an extremely deep network with 152 layers using residual
connections and bottleneck blocks. It is designed for maximum accuracy, often
serving as a backbone in state-of-the-art models for classification, detection,
and segmentation tasks.`,

  // MobileNet models
  MobileNetV1: `MobileNetV1 is a lightweight convolutional neural network optimized for
mobile and embedded applications. It uses depthwise separable convolutions to
reduce computation and parameters while maintaining reasonable accuracy.`,

  MobileNetV2: `MobileNetV2 introduces inverted residuals and linear bottleneck layers,
further reducing model size and computation. It improves feature reuse and maintains
accuracy for mobile and edge devices, making it suitable for real-time vision tasks.`,

  MobileNetV3: `MobileNetV3 is a highly optimized network for mobile vision applications.
It incorporates squeeze-and-excitation (SE) blocks, hard-swish activation, and
architecture search to maximize efficiency. MobileNetV3 offers small and large
variants to balance between performance and computation requirements.`,
};

export default modelDescriptions;
