import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigatewayv2";
import * as apiIntegrations from "aws-cdk-lib/aws-apigatewayv2-integrations";
import { Construct } from "constructs";
import * as path from "path";
import { execSync } from "child_process";

export class CcfDemoStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ---------------------------------------------------------------
    // S3 bucket for static data (JSON exports) and frontend assets
    // ---------------------------------------------------------------
    const dataBucket = new s3.Bucket(this, "DataBucket", {
      bucketName: cdk.PhysicalName.GENERATE_IF_NEEDED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      cors: [
        {
          allowedMethods: [s3.HttpMethods.GET],
          allowedOrigins: ["*"],
          allowedHeaders: ["*"],
        },
      ],
    });

    const frontendBucket = new s3.Bucket(this, "FrontendBucket", {
      bucketName: cdk.PhysicalName.GENERATE_IF_NEEDED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    });

    // ---------------------------------------------------------------
    // Lambda – interactive a priori rule runner
    // Pre-bundle with esbuild locally (no Docker required)
    // ---------------------------------------------------------------
    const lambdaDir = path.join(__dirname, "../../lambda");
    const lambdaOut = path.join(lambdaDir, "dist");

    // Bundle at synth time using local esbuild
    execSync(
      [
        "npx esbuild src/handler.ts",
        "--bundle",
        "--platform=node",
        "--target=node20",
        "--format=esm",
        "--outfile=dist/index.mjs",
        "--external:@aws-sdk/*",
        "--minify",
        "--sourcemap",
      ].join(" "),
      { cwd: lambdaDir, stdio: "inherit" },
    );

    const aprioriLambda = new lambda.Function(this, "AprioriFn", {
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: "index.handler",
      code: lambda.Code.fromAsset(lambdaOut),
      memorySize: 512,
      timeout: cdk.Duration.seconds(15),
      environment: {
        DATA_BUCKET: dataBucket.bucketName,
        NODE_OPTIONS: "--enable-source-maps",
      },
    });

    dataBucket.grantRead(aprioriLambda);

    // ---------------------------------------------------------------
    // HTTP API Gateway
    // ---------------------------------------------------------------
    const httpApi = new apigateway.HttpApi(this, "HttpApi", {
      apiName: "ccf-demo-api",
      corsPreflight: {
        allowOrigins: ["*"],
        allowMethods: [apigateway.CorsHttpMethod.GET, apigateway.CorsHttpMethod.POST],
        allowHeaders: ["Content-Type"],
      },
    });

    const lambdaIntegration = new apiIntegrations.HttpLambdaIntegration(
      "AprioriIntegration",
      aprioriLambda,
    );

    httpApi.addRoutes({
      path: "/api/run-rules",
      methods: [apigateway.HttpMethod.POST],
      integration: lambdaIntegration,
    });

    httpApi.addRoutes({
      path: "/api/items",
      methods: [apigateway.HttpMethod.GET],
      integration: lambdaIntegration,
    });

    httpApi.addRoutes({
      path: "/api/items/{itemId}",
      methods: [apigateway.HttpMethod.GET],
      integration: lambdaIntegration,
    });

    httpApi.addRoutes({
      path: "/api/rules",
      methods: [apigateway.HttpMethod.GET],
      integration: lambdaIntegration,
    });

    httpApi.addRoutes({
      path: "/api/stats",
      methods: [apigateway.HttpMethod.GET],
      integration: lambdaIntegration,
    });

    httpApi.addRoutes({
      path: "/api/claims",
      methods: [apigateway.HttpMethod.GET],
      integration: lambdaIntegration,
    });

    httpApi.addRoutes({
      path: "/api/config",
      methods: [apigateway.HttpMethod.GET],
      integration: lambdaIntegration,
    });

    // ---------------------------------------------------------------
    // CloudFront – single distribution for frontend + data + API
    // ---------------------------------------------------------------
    const oai = new cloudfront.OriginAccessIdentity(this, "OAI");
    frontendBucket.grantRead(oai);
    dataBucket.grantRead(oai);

    const distribution = new cloudfront.Distribution(this, "Distribution", {
      defaultBehavior: {
        origin: new origins.S3Origin(frontendBucket, {
          originAccessIdentity: oai,
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
      },
      additionalBehaviors: {
        "/data/*": {
          origin: new origins.S3Origin(dataBucket, {
            originAccessIdentity: oai,
          }),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        },
        "/api/*": {
          origin: new origins.HttpOrigin(
            `${httpApi.httpApiId}.execute-api.${this.region}.amazonaws.com`,
          ),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy:
            cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        },
      },
      defaultRootObject: "index.html",
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: "/index.html",
          ttl: cdk.Duration.seconds(0),
        },
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: "/index.html",
          ttl: cdk.Duration.seconds(0),
        },
      ],
    });

    // ---------------------------------------------------------------
    // Deploy frontend build to S3
    // ---------------------------------------------------------------
    new s3deploy.BucketDeployment(this, "DeployFrontend", {
      sources: [s3deploy.Source.asset(path.join(__dirname, "../../frontend/dist"))],
      destinationBucket: frontendBucket,
      distribution,
      distributionPaths: ["/*"],
    });

    // ---------------------------------------------------------------
    // Outputs
    // ---------------------------------------------------------------
    new cdk.CfnOutput(this, "DistributionUrl", {
      value: `https://${distribution.distributionDomainName}`,
      description: "CloudFront URL for the demo",
    });

    new cdk.CfnOutput(this, "ApiUrl", {
      value: httpApi.url ?? "",
      description: "HTTP API Gateway URL (direct, bypasses CloudFront)",
    });

    new cdk.CfnOutput(this, "DataBucketName", {
      value: dataBucket.bucketName,
      description: "S3 bucket for export data (upload with: npm run upload-data)",
    });

    new cdk.CfnOutput(this, "FrontendBucketName", {
      value: frontendBucket.bucketName,
      description: "S3 bucket for frontend assets",
    });
  }
}
